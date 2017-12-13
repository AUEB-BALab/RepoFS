#!/usr/bin/env python

import os
import argparse

from time import time
from stat import S_IFDIR, S_IFREG
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from gitoper import GitOperations
from cache import Cache


class RepoFS(Operations):
    def __init__(self, repo, nocache):
        self.repo = repo
        self.nocache = nocache
        self._git = GitOperations(repo)
        if not nocache:
            self._cache = Cache()

    def _get_root(self):
        return ['commits']

    def _get_commits(self):
        if self._cache:
            commits = self._cache.get_commit_names()
            if commits: # commits exist on cache
                return commits

            # no cache entry, get commits and store in cache
            commits = self._git.commits()
            self._cache.store_commits(commits)
            return commits

        return self._git.commits() # if no cache get them from git

    def _commit_metadata_names(self):
        return ['.git-log', '.git-parents', '.git-descendants', '.git-names']

    def _git_path(self, path):
        if path.count("/") == 2:
            return ""

        return path.split("/", 3)[-1]

    def _commit_from_path(self, path):
        return path.split("/")[2]

    def _get_commit(self, path):
        dirents = self._git.directory_contents(self._commit_from_path(path), self._git_path(path))
        if path.count("/") == 2:
            dirents += self._commit_metadata_names()
        return dirents

    def _is_dir(self, path):
        if path == "/":
            return True

        if path.startswith("/commits"):
            if path =="/commits" or path.count("/") == 2:
                return True
            else:
                return self._git.is_dir(self._commit_from_path(path), self._git_path(path))

        return False

    def _get_file_size(self, path):
        # return self._git.file_size(self._git_path(path))
        return 0

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()
        st = dict(st_uid=uid, st_gid=gid)
        if self._is_dir(path):
            st['st_mode'] = (S_IFDIR | 0o440)
            st['st_nlink'] = 2
        else:
            st['st_mode'] = (S_IFREG | 0o440)
            st['st_size'] = self._get_file_size(path)

        st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
        return st

    def readdir(self, path, fh):
        dirents = ['.', '..']
        if path == "/":
            dirents.extend(self._get_root())
        elif path.startswith("/commits"):
            if path == "/commits":
                dirents.extend(self._get_commits())
            elif path.count("/") >= 2: #/commits/commithash
                dirents.extend(self._get_commit(path))

        for r in dirents:
            yield r



    statfs=None
    readlink=None

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


def main(repo, mount, nocache):
    if not os.path.exists(os.path.join(repo, '.git')):
        raise Exception("Not a git repository")

    FUSE(RepoFS(repo, nocache), mount, nothreads=True, foreground=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Git repository to be processed.")
    parser.add_argument("mount", help="Path where the FileSystem will be mounted." \
    "If it doesn't exist it is created and if it exists and contains files RepoFS exits.")
    parser.add_argument(
        "-nocache",
        "--nocache",
        help="Do not cache repository metadata. FileSystem updates when the repository changes.",
        action="store_true",
        default=False
    )
    args = parser.parse_args()

    main(args.repo, args.mount, args.nocache)

