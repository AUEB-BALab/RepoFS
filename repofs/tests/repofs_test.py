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

import os

from unittest import TestCase, main
from os import mkdir, rmdir, errno, path
from fuse import FuseOSError

from repofs.repofs import RepoFS, RepoFSError
from repofs.handlers.ref import RefHandler
from repofs.handlers.commit_hash import CommitHashHandler
from repofs.handlers.commit_date import CommitDateHandler


class RepoFSTestCase(TestCase):
    def setUp(self):
        self.mount = 'mnt'
        self.mount2 = 'mnt2'
        self.mount3 = 'mn3'
        try:
            mkdir(self.mount)
            mkdir(self.mount2)
            mkdir(self.mount3)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        self.repofs = RepoFS('test_repo', self.mount, False, False, False)
        self.repofs_htree = RepoFS('test_repo', self.mount2, True, False, False)
        self.repofs_nosym = RepoFS('test_repo', self.mount3, False, True, False)
        self.first_commit = '/commits-by-date/2005/6/7/' + list(self.repofs._git.commits_by_date(2005, 6, 7))[0]
        self.second_commit = '/commits-by-date/2005/6/10/' + list(self.repofs._git.commits_by_date(2005, 6, 10))[0]
        self.recent_commit = '/commits-by-date/2009/10/11/' + list(self.repofs._git.commits_by_date(2009, 10, 11))[0]
        rcommit = list(self.repofs._git.commits_by_date(2009, 10, 11))[0]
        self.recent_commit_by_hash = '/commits-by-hash/' + rcommit
        self.recent_commit_by_hash_tree = os.path.join('/commits-by-hash', self.hex_path(rcommit), rcommit)

    def hex_path(self, c):
        return os.path.join(c[:2], c[2:4], c[4:6])

    def test_readdir(self):
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/', None)), 6)
        self.assertTrue('tags' in self.repofs.readdir('/', None))
        self.assertTrue('branches' in self.repofs.readdir('/', None))
        self.assertTrue('commits-by-date' in self.repofs.readdir('/', None))
        self.assertTrue('commits-by-hash' in self.repofs.readdir('/', None))

    def test_target_from_symlink(self):
        first_commit = self.first_commit.split("/")[-1]
        second_commit = self.second_commit.split("/")[-1]

        self.assertEqual(self.repofs._target_from_symlink('/tags/t20091011ca'),
                path.join(self.mount, self.recent_commit_by_hash[1:], ''))
        self.assertEqual(self.repofs._target_from_symlink('/branches/heads/master'),
                path.join(self.mount, self.recent_commit_by_hash[1:], ''))
        self.assertEqual(self.repofs._target_from_symlink('/branches/heads/master'),
                path.join(self.repofs.mount, self.recent_commit_by_hash[1:], ''))
        self.assertEqual(self.repofs._target_from_symlink(
                path.join(self.second_commit, '.git-parents', first_commit)),
                path.join(self.repofs.mount, 'commits-by-hash', first_commit, ""))
        self.assertEqual(self.repofs._target_from_symlink(
                path.join('/', 'commits-by-hash', second_commit, '.git-parents', first_commit)),
                path.join(self.repofs.mount, 'commits-by-hash', first_commit, ""))
        self.assertEqual(self.repofs_htree._target_from_symlink(
                path.join('/', 'commits-by-hash', self.repofs_htree._commit_hex_path(second_commit), second_commit, '.git-parents', first_commit)),
                path.join(self.repofs_htree.mount, 'commits-by-hash', self.repofs_htree._commit_hex_path(first_commit), first_commit, ""))
        commit = self.repofs._git.commit_of_ref("refs/tags/t20070115la").split("/")[-1]
        self.assertEqual(self.repofs._target_from_symlink(path.join('/commits-by-hash', commit, "link_a")),
                path.join(self.repofs.mount, "commits-by-hash", commit, "file_a"))
        self.assertEqual(self.repofs_htree._target_from_symlink(
                path.join('/', 'commits-by-hash', self.repofs_htree._commit_hex_path(commit), commit, "link_a")),
                path.join(self.repofs_htree.mount, "commits-by-hash", self.repofs_htree._commit_hex_path(commit), commit, "file_a"))
        self.assertEqual(self.repofs._target_from_symlink(path.join('/commits-by-date/2007/1/15', commit, "link_a")),
                path.join(self.repofs.mount, "commits-by-date/2007/1/15", commit, "file_a"))

    def test_access_non_existent_dir(self):
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/foobar", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/tags/barfoo", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/branches/barfoo", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs_nosym.readdir("/branches/barfoo", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/commits-by-date/helloworld", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/commits-by-date/2005/helloworld", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/commits-by-date/2005/6/helloworld", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/commits-by-date/2005/6/7/helloworld", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir(self.first_commit + "/dir_a/helloworld", None).next()
        with self.assertRaises(FuseOSError):
            self.repofs.readdir("/commits-by-hash/helloworld", None).next()

    def test_access_non_existent_file(self):
        with self.assertRaises(FuseOSError):
            self.repofs.read(self.first_commit + "/dir_a/helloworld", 100, 10, None)

    def test_st_time(self):
        ctime = self.repofs._git.get_commit_time(self.recent_commit_by_hash.split("/")[-1])

        st = self.repofs.getattr(self.recent_commit + "/dir_a")
        self.assertEqual(st['st_mtime'], ctime)
        self.assertEqual(st['st_ctime'], ctime)
        self.assertNotEqual(st['st_atime'], ctime)

        st = self.repofs.getattr(self.recent_commit + "/file_a")
        self.assertEqual(st['st_mtime'], ctime)
        self.assertEqual(st['st_ctime'], ctime)
        self.assertNotEqual(st['st_atime'], ctime)

    def test_get_handler(self):
        self.assertTrue(isinstance(self.repofs._get_handler("/commits-by-hash"), CommitHashHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/commits-by-hash/foo"), CommitHashHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/commits-by-date"), CommitDateHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/commits-by-date/foo"), CommitDateHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/branches"), RefHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/branches/foo"), RefHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/tags"), RefHandler))
        self.assertTrue(isinstance(self.repofs._get_handler("/tags/foo"), RefHandler))

if __name__ == "__main__":
    main()
