#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import fuse
import argparse

from fuse import FUSE, FuseOSError, Operations
from subprocess import check_output, CalledProcessError


class Cache(object):
    def __init__(self):
        self._storage = {}

    def store_commits(self, commitNames):
        if 'commits' not in self._storage:
            self._storage['commits'] = {}

        for commit in commitNames:
            self._storage['commits'][commit] = {}

    def store_commit_data(self, chash, data):
        self._storage['commits'][chash] = data

    def store_tag(self, tag, chash):
        if 'tags' not in self._storage:
            self._storage['tags'] = {}

        self._storage['tags'][tag] = chash

    def store_branch(self, branch, chash):
        if 'branches' not in self._storage:
            self._storage['branches'] = {}

        self._storage['branches'][branch] = chash

    def get_commit_names(self):
        if 'commits' not in self._storage:
            return None

        return self._storage['commits'].keys()

    def get_commit_data(self, chash):
        if 'commits' not in self._storage or\
                chash not in self._storage['commits'] or\
                not self._storage['commits'][chash]:
            return None

        return self._storage['commits'][chash]

    def get_tags(self):
        if 'tags' not in self._storage:
            return None

        return self._storage['tags']

    def get_branches(self):
        if 'branches' not in self._storage:
            return None

        return self._storage['branches']


class GitOperations(object):
    def __init__(self, repo):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')

    def get_branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        branchrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                '--format=%(objectname) %(refname)', 'refs/heads/']).splitlines()
        branches = [ref.strip() for ref in branchrefs]
        return branches

    def get_tags(self):
        """
        Returns tags in the form:
        <commit_hash> refs/tags/<tagname>
        """
        tagrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                '--format=%(objectname) %(refname)', 'refs/tags/']).splitlines()
        tags = [ref.strip() for ref in tagrefs]
        return tags

    def get_commits(self):
        """
        Returns a list of commit hashes
        """
        commits = check_output(['git', '--git-dir', self._gitrepo,\
                'log', '--pretty=format:%H']).splitlines()
        commits = [commit.strip() for commit in commits]
        return commits

    def get_commit_data(self):
        """
        Returns a dictionary containing commit data
        Data includes log, parents, descendants, names
        """
        data = {}
        data['log'] = check_output(['git', '--git-dir', self._gitrepo, 'log', commit])
        #data['parents'] = ...
        #data['descendants'] = ...
        #data['names'] = ...
        return data



class RepoFS(Operations):
    def __init__(self, repo, nocache):
        self.repo = repo
        self.nocache = nocache
        self._git = GitOperations(repo)
        if not nocache:
            self._cache = Cache()

    readdir=None
    statfs=None
    readlink=None
    getattr=None

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

