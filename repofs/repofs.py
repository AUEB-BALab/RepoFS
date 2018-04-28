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
import datetime
import os
import sys

from time import time
from stat import S_IFDIR, S_IFREG, S_IFLNK, S_IWUSR
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from gitoper import GitOperations, GitOperError
from handlers.ref import RefHandler
from handlers.commit_hash import CommitHashHandler
from handlers.commit_date import CommitDateHandler
from handlers.root import RootHandler


class RepoFS(Operations):
    def __init__(self, repo, mount, hash_trees, no_ref_symlinks):
        self.repo = repo
        self.repo_mode = os.stat(repo).st_mode
        self.no_ref_symlinks = no_ref_symlinks
        # remove write permission and directory flag
        self.mnt_mode = self.repo_mode & ~S_IWUSR & ~S_IFDIR
        self.mount = mount
        self.hash_trees = hash_trees
        self._git = GitOperations(repo)
        self._branch_refs = ['refs/heads/', 'refs/remotes/']
        self._tag_refs = ['refs/tags']

    def _hash_updir(self, c):
        if not self.hash_trees:
            return ""
        return os.path.join(c[:2], c[2:4], c[4:6])

    def _format_to_link(self, commit):
        """ Return the specified commit as a symbolic link to
        commits-by-hash"""
        return os.path.join(self.mount, "commits-by-hash", self._hash_updir(commit), commit) + "/"

    def _commit_hex_path(self, commit):
        if not self.hash_trees:
            return ""

        return os.path.join(commit[:2], commit[2:4], commit[4:6])

    def _target_from_symlink(self, path):
        handler = self._get_handler(path)
        if handler.is_metadata_symlink():
            target = handler.get_symlink_target()
            return os.path.join(self.mount, "commits-by-hash", self._commit_hex_path(target), target, "")
        elif path.startswith("/commits-by-date"):
            return os.path.join(self.mount, "commits-by-date", handler.get_symlink_target())
        elif path.startswith("/commits-by-hash"):
            return os.path.join(self.mount, "commits-by-hash", handler.get_symlink_target())
        elif path.startswith("/branches/") or path.startswith("/tags/"):
            return self._format_to_link(handler.get_commit())
        else:
            raise FuseOSError(errno.ENOENT)

    def get_commit_time(self, commit):
        return self._git.get_commit_time(commit)

    def _get_handler(self, path):
        if path == "/":
            return RootHandler()
        elif path.startswith("/commits-by-hash"):
            return CommitHashHandler(path[17:], self._git, self.hash_trees)
        elif path.startswith("/commits-by-date"):
            return CommitDateHandler(path[17:], self._git)
        elif path.startswith("/branches"):
            return RefHandler(path[10:], self._git, self._branch_refs, self.no_ref_symlinks)
        elif path.startswith("/tags"):
            return RefHandler(path[1:], self._git, self._tag_refs, self.no_ref_symlinks)
        else:
            raise FuseOSError(errno.ENOENT)

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()
        st = dict(st_uid=uid, st_gid=gid)
        handler = self._get_handler(path)
        try:
            if handler.is_dir():
                st['st_mode'] = (S_IFDIR | self.mnt_mode)
                st['st_nlink'] = 2
            elif handler.is_symlink():
                st['st_mode'] = (S_IFLNK | self.mnt_mode)
                st['st_nlink'] = 1
                st['st_size'] = len(self._target_from_symlink(path))
            else:
                st['st_mode'] = (S_IFREG | self.mnt_mode)
                st['st_size'] = handler.file_size()
        except GitOperError:
            raise FuseOSError(errno.ENOENT)

        t = time()
        st['st_atime'] = st['st_ctime'] = st['st_mtime'] = t

        commit_time = -1
        if handler and hasattr(handler, "get_commit") and handler.get_commit():
            commit_time = self.get_commit_time(handler.get_commit())

        if commit_time != -1:
            st['st_ctime'] = st['st_mtime'] = commit_time

        return st

    def readdir(self, path, fh):
        dirents = ['.', '..']
        handler = self._get_handler(path)
        dirents.extend(handler.readdir())

        for r in dirents:
            yield r


    def read(self, path, size, offset, fh):
        handler = self._get_handler(path)
        try:
            contents = handler.file_contents()
        except GitOperError:
            raise FuseOSError(errno.ENOENT)

        return contents[offset:offset + size]

    def readlink(self, path):
        return self._target_from_symlink(path)


    statfs=None

    access=None
    chmod=None
    chown=None
    mknod=None
    rmdir=None
    mkdir=None
    unlink=None
    symlink=None
    rename=None
    link=None
    utimens=None


class RepoFSError(Exception):
    pass
