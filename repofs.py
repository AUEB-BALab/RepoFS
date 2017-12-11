#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import fuse
import argparse

from fuse import FUSE, FuseOSError, Operations
from subprocess import check_output, CalledProcessError


CACHE={}

def fill_cache(repo):
    """
    fill cache
    cache contains 3 keys: commits, tags and branches
    cache = {
        commits: {
            commitHash1: {
                log: "log1",
                parents: [parentHash11, parentHash12, ..., parentHash1K],
                descendants: [descHash11, descHash12, ..., descHash1K],
                names: [branch11, tag11, ...]
            },
            ...,
            commitHashN: {
                ...
            }
        },
        tags: {
            tagName1: commitHash1,
            ...,
            tagNameN: commitHashN
        },
        branches: {
            branchName1: commitHash1,
            ...,
            branchNameN: commitHashN
        }
    }
    """
    CACHE = {
        'commits': {},
        'tags': {},
        'branches': {}
    }

    gitrepo = os.path.join(repo, '.git')

    commits = check_output(['git', '--git-dir', gitrepo,\
            'log', '--pretty=format:%H']).splitlines()
    branchrefs = check_output(['git', '--git-dir', gitrepo, 'for-each-ref',\
            '--format=%(objectname) %(refname)', 'refs/heads/']).splitlines()
    tagrefs = check_output(['git', '--git-dir', gitrepo, 'for-each-ref',\
            '--format=%(objectname) %(refname)', 'refs/tags/']).splitlines()

    commits = [commit.strip() for commit in commits]
    branchrefs = [ref.strip() for ref in branchrefs]
    tagrefs = [ref.strip() for ref in tagrefs]

    for commit in commits:
        commitLog = check_output(['git', '--git-dir', gitrepo, 'log', commit])
        commitDict = {}
        commitDict['log'] = commitLog
        #commitDict['parents'] = ...
        #commitDict['descendants'] = ...
        commitDict['names'] = []
        CACHE['commits'][commit] = commitDict

    for ref in branchrefs:
        chash, refName = ref.split(' ')
        branchName = refName.split('/')[2]
        CACHE['branches'][branchName] = chash
        CACHE['commits'][chash]['names'].append(branchName)

    for ref in tagrefs:
        chash, refName = ref.split(' ')
        tagName = refName.split('/')[2]
        CACHE['tags'][tagName] = chash
        CACHE['commits'][chash]['names'].append(tagName)


def main(repo, mount, nocache):
    if not os.path.exists(os.path.join(repo, '.git')):
        raise Exception("Not a git repository")

    if not nocache:
        print "Filling cache..."
        fill_cache(repo)

    print "Ready!"

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
