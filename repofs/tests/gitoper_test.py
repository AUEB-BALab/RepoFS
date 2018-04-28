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

import datetime

from unittest import TestCase, main
from repofs.gitoper import GitOperations, GitOperError


class GitOperationsTestCase(TestCase):
    def setUp(self):
        self.go = GitOperations('test_repo')
        self.master_hash = self.go.commit_of_ref("master").split("/")[-1]

    def test_cached_command(self):
        self.assertEquals(self.go.cached_command(['show', 'master:file_r']),
                          "phantom\n")
        self.go.cached_command(['rm', 'file_r'])
        # Retrieve removed command from cache
        self.assertEquals(self.go.cached_command(['show', 'master:file_r']),
                          "phantom\n")

    def test_first_year(self):
        self.assertEquals(self.go._first_year(), 2005)

    def test_last_year(self):
        self.assertEquals(self.go._last_year(), 2009)

    def test_years(self):
        self.assertEquals(self.go.years, [2005, 2006, 2007, 2008, 2009])

    def test_commits_by_date(self):
        self.assertEquals(len(self.go.commits_by_date(2009,10,11)), 2)
        self.assertEquals(len(self.go.commits_by_date(2009,10,12)), 0)

    def test_all_commits(self):
        self.assertGreater(len(list(self.go.all_commits())), 3)

    def test_file_size(self):
        self.assertTrue(self.go.file_size(self.master_hash, "file_a") > 0)
        self.assertEqual(self.go.file_size(self.master_hash, "file_b"), 0)

    def test_file_contents(self):
        self.assertEqual(self.go.file_contents(self.master_hash, "file_a"), "Contents\n")

    def test_is_dir(self):
        self.assertTrue(self.go.is_dir(self.master_hash, "dir_a"))
        self.assertTrue(self.go.is_dir(self.master_hash, "dir_a/dir_b"))
        self.assertTrue(self.go.is_dir(self.master_hash, "dir_a/dir_b/dir_c"))

        self.assertFalse(self.go.is_dir(self.master_hash, "dir_a/dir_b/dir_c/dir_d"))
        self.assertFalse(self.go.is_dir(self.master_hash, "dir_a/dir_a"))
        self.assertFalse(self.go.is_dir(self.master_hash, "file_a"))

    def test_directory_contents(self):
        self.assertEqual(self.go.directory_contents(self.master_hash, "dir_a"), ["dir_b", "file_aa"])
        self.assertEqual(self.go.directory_contents(self.master_hash, "dir_a/dir_b"), ["dir_c"])

    def test_non_existent(self):
        with self.assertRaises(GitOperError):
            self.go.file_size(self.master_hash, "file_z")
        with self.assertRaises(GitOperError):
            self.go.file_size(self.master_hash, "dir_z/file_z")
        with self.assertRaises(GitOperError):
            self.assertEqual(self.go.directory_contents(self.master_hash, "dir_z"), [])
        with self.assertRaises(GitOperError):
            self.assertEqual(self.go.directory_contents(self.master_hash, "dir_z/dir_zz"), [])

    def test_fill_trees(self):
        dirs = ["dir_a", "dir_a/dir_b"]
        trees = [(d, "tree") for d in dirs]
        diff = [("file_a", "blob"), ("file_b", "dunno")]

        self.go._fill_trees(self.master_hash, trees + diff)
        self.assertEqual(self.go._trees[self.master_hash], set(dirs))

        self.go._fill_trees(self.master_hash, trees + diff)
        self.assertEqual(self.go._trees[self.master_hash], set(dirs))

    def test_get_tree(self):
        self.assertEqual(self.go._get_tree(self.master_hash, "dir_a"), [("dir_b", "tree"), ("file_aa", "blob")])
        self.assertEqual(self.go._get_tree(self.master_hash, ""), [("dir_a", "tree")] + [("file_" + c, "blob") for c in "abcdr"] + [("link_a", "blob")])

    def test_cache_trees(self):
        self.go._cache_tree(self.master_hash, "dir_a")

        self.assertEqual(self.go._trees[self.master_hash], set(["dir_a/dir_b"]))
        self.assertEqual(self.go._trees_filled[self.master_hash], set(["dir_a"]))

    def test_commit_time(self):
        self.assertEqual("2009-10-11", datetime.datetime.fromtimestamp(self.go.get_commit_time(self.master_hash)).strftime("%Y-%m-%d"))

    def test_is_symlink(self):
        commit = self.go.commit_of_ref("refs/tags/t20070115la").split("/")[-1]
        self.assertTrue(self.go.is_symlink(commit, "link_a"))
        self.assertFalse(self.go.is_symlink(commit, "file_a"))

    def test_author(self):
        commit = self.go.commit_of_ref("refs/tags/t20070115la").split("/")[-1]
        self.assertEqual(self.go.author(commit), "repofs")
        self.assertEqual(self.go.author_email(commit), "repofs@repofs.com")
        pass


if __name__ == "__main__":
    main()
