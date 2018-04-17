#!/usr/bin/env python
#
# Copyright 2017-2018 Vitalis Salis and Diomidis Spinellis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import errno

from repofs.handlers.handler_base import HandlerBase
from repofs import utils
from fuse import FuseOSError

BRANCH_TYPE = "BRANCH"
TAG_TYPE = "TAG"
BRANCH_REFS = ['refs/heads/', 'refs/remotes/']
TAG_REFS = ['refs/tags']
class RefHandler(HandlerBase):
    def __init__(self, path, oper, refs, no_ref_symlinks):
        self.path = path
        self.oper = oper
        self.no_ref_symlinks = no_ref_symlinks
        self.refs = self.oper.refs(refs)
        self.path_data = utils.demux_ref_path(path, self.refs)
        self.types = ['tags', 'heads', 'remotes']

    def _is_ref_prefix(self):
        elements = self.path_data['ref'].split("/")
        for ref in self.refs:
            ref = ref.split('/')[1:]
            if elements == ref[:len(elements)] and len(elements) < len(ref):
                return True
        return False

    def _get_refs(self):
        """Return the ref elements that match the specified path and
        refs, e.g. refs/heads or refs/tags. """
        ref_prefix = []
        if self.path_data['ref']:
            ref_prefix = self.path_data['ref'].split("/")
        result = set()
        # Find common prefix
        for ref in self.refs:
            ref = ref.split('/')[1:]
            if ref_prefix == ref[:len(ref_prefix)]:
                # Common prefix found
                if len(ref) > len(ref_prefix):
                    result.add(ref[len(ref_prefix)])

        return list(result)

    def _is_full_ref(self):
        """Return true if the specified path (e.g. branches/master, or
        tags/V1.0) refers to one of the specified refs, (e.g.
        refs/heads or refs/tags). """
        for ref in self.refs:
            ref = ref.split('/')[1:]
            # print('Check path [%s] == ref [%s]' % (path, ref))
            if self.path_data['ref'] == "/".join(ref):
                return True
        return False

    def get_commit(self):
        if self._is_full_ref():
            return self.oper.commit_of_ref(self.path_data['ref'])
        return ""

    def is_dir(self):
        if not self.path_data['ref'] or self.path_data['ref'] in self.types:
            return True

        if self._is_ref_prefix():
            return True
        if self.no_ref_symlinks:
            if self.path_data['type'] not in self.types:
                return False
            if not self._is_full_ref():
                return False
            return self._is_metadata_dir() or self.oper.is_dir(self.get_commit(), self.path_data['commit_path'])
        return False


    def is_symlink(self):
        if (self.is_metadata_symlink() or
                (self._is_full_ref() and not self.no_ref_symlinks)):
            return True
        return False

    def file_contents(self):
        commit = self.get_commit()
        if self._is_metadata_file():
            return self._get_metadata_file(self.path_data['commit'])

        return self.oper.file_contents(commit, self.path_data['commit_path'])

    def file_size(self):
        if self._is_metadata_file():
            return len(self._get_metadata_file(self.path_data['commit']))

        return self.oper.file_size(self.get_commit(), self.path_data['commit_path'])

    def get_symlink_target(self):
        return self.get_commit()

    def readdir(self):
        if not self.path:
            return self._get_refs()

        if not self._is_ref_prefix() and not self._is_full_ref():
            raise FuseOSError(errno.ENOENT)

        if self._is_ref_prefix():
            return self._get_refs()
        elif self.no_ref_symlinks and self._is_full_ref():
            if self._is_metadata_dir():
                return self._get_metadata_dir(self.get_commit())
            else:
                dirents = self.oper.directory_contents(self.get_commit(), self.path_data['commit_path'])
                if not self.path_data['commit_path']:
                    dirents += self._get_metadata_names()

            return dirents
        else:
            raise FuseOSError(errno.ENOENT)
