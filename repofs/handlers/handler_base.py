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

from fuse import FuseOSError
from repofs import utils

class HandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def is_dir(self, *args, **kwargs):
        raise NotImplementedError("is_dir not implemented in child class")

    def is_symlink(self, *args, **kwargs):
        raise NotImplementedError("is_symlink not implemented in child class")

    def file_contents(self, *args, **kwargs):
        raise NotImplementedError("file_contents not implemented in child class")

    def readdir(self, *args, **kwargs):
        raise NotImplementedError("readdir not implemented in child class")

    def _get_metadata_dir(self, commit):
        metaname = self.path_data['commit_path']
        if metaname == '.git-parents':
            return self.oper.commit_parents(commit)
        elif metaname == '.git-descendants':
            return self.oper.commit_descendants(commit)
        elif metaname == '.git-names':
            return self.oper.commit_names(commit)
        else:
            return []

    def _get_metadata_file(self, commit):
        metaname = self.path_data['commit_path']
        if metaname == ".author":
            return self.oper.author(commit)
        elif metaname == ".author-email":
            return self.oper.author_email(commit)
        else:
            self._not_exists()

    def _is_metadata_dir(self):
        return utils.is_metadata_dir(self.path_data['commit_path'])

    def _is_metadata_file(self):
        return utils.is_metadata_file(self.path_data['commit_path'])

    def _is_metadata_name(self):
        return self._is_metadata_dir() or self._is_metadata_file()

    def is_metadata_symlink(self):
        return utils.is_metadata_symlink(self.path_data['commit_path'], self.oper.all_commits())

    def _get_metadata_names(self):
        return utils.metadata_names()

    def _is_metadata_symlink(self):
        return utils.is_metadata_symlink(self.path_data['commit_path'], self.oper.all_commits())

    def _not_exists(self):
        raise FuseOSError(errno.ENOENT)

    def _dir_not_exists(self):
        raise FuseOSError(errno.ENOTDIR)
