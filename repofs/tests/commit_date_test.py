#!/usr/bin/env python
#
# Copyright 2017-2021 Vitalis Salis and Diomidis Spinellis
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
import errno

from unittest import TestCase, main
from fuse import FuseOSError

from repofs.repofs import RepoFS
from repofs import utils
from repofs.handlers.commit_date import CommitDateHandler

class CommitDateHandlerTest(TestCase):
    def setUp(self):
        self.mount = 'mnt'
        try:
            os.mkdir(self.mount)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        self.repofs = RepoFS('test_repo', self.mount, True, False, False)

    def generate(self, path):
        oper = self.repofs._git
        return CommitDateHandler(path, oper)

    def test_is_dir(self):
        recent_commit = '2009/10/11/' + list(self.repofs._git.commits_by_date(2009, 10, 11))[0]

        self.assertTrue(self.generate("").is_dir())
        self.assertTrue(self.generate("2005").is_dir())
        self.assertTrue(self.generate("2005/7").is_dir())
        self.assertTrue(self.generate("2005/7/1").is_dir())
        self.assertTrue(self.generate("2005/6/7").is_dir())
        self.assertTrue(self.generate(recent_commit).is_dir())
        self.assertTrue(self.generate(recent_commit + '/dir_a').is_dir())
        self.assertTrue(self.generate(recent_commit + '/dir_a/dir_b').is_dir())
        self.assertTrue(self.generate(recent_commit + '/dir_a/dir_b/dir_c').is_dir())
        self.assertFalse(self.generate(recent_commit + '/file_a').is_dir())
        self.assertFalse(self.generate(recent_commit + '/.git-log').is_dir())
        self.assertFalse(self.generate(recent_commit + '/dir_a/file_aa').is_dir())
        with self.assertRaises(FuseOSError):
            self.generate('lala').is_dir()
        with self.assertRaises(FuseOSError):
            self.generate('2005/lala').is_dir()
        with self.assertRaises(FuseOSError):
            self.generate('2005/7/lala').is_dir()

    def test_is_symlink(self):
        all_commits = list(self.repofs._git.all_commits())
        last_commit = all_commits[0]
        pre_last_commit = all_commits[1]

        recent_commit = '2009/10/11/' + last_commit
        self.assertFalse(self.generate("").is_symlink())
        self.assertFalse(self.generate("2007").is_symlink())
        self.assertFalse(self.generate("2007/01").is_symlink())
        self.assertFalse(self.generate("2007/01/15").is_symlink())
        self.assertFalse(self.generate("2007/1/15/").is_symlink())
        self.assertFalse(self.generate(recent_commit).is_symlink())
        self.assertFalse(self.generate(recent_commit + "/.git-parents").is_symlink())
        self.assertTrue(self.generate(recent_commit + "/.git-parents/" + pre_last_commit).is_symlink())

    def test_readdir(self):
        all_commits = list(self.repofs._git.all_commits())
        last_commit = all_commits[0]
        contents_of_last = self.repofs._git.directory_contents(last_commit, "")
        contents_of_last_dira = self.repofs._git.directory_contents(last_commit, "dir_a")

        self.assertEqual(len(list(self.generate("").readdir())), len(list(self.repofs._git.years)))
        self.assertEqual(len(list(self.generate("2007").readdir())), 12)
        self.assertEqual(len(list(self.generate("2007/10").readdir())), self.generate("2007")._days_per_month(2007)[9])
        self.assertEqual(self.generate("2009/10/11/" + last_commit).readdir(), contents_of_last + utils.metadata_names())
        self.assertEqual(self.generate("2009/10/11/" + last_commit + "/dir_a").readdir(), contents_of_last_dira)

        self.assertEqual(len(self.generate("").readdir()), 5)
        self.assertEqual(len(self.generate("2005").readdir()), 12)
        self.assertEqual(len(self.generate("2005/06").readdir()), 30)
        self.assertEqual(len(list(self.generate("2005/06/7").readdir())), 1)
        self.assertEqual(len(list(self.generate("2005/06/06").readdir())), 0)
        self.assertEqual(len(list(self.generate("2005/6/08").readdir())), 0)
        self.assertEqual(len(list(self.generate("2005/6/29").readdir())), 0)
        self.assertEqual(len(list(self.generate("2005/6/30").readdir())), 1)
        self.assertEqual(len(list(self.generate("2005/7/1").readdir())), 2)
        self.assertEqual(len(list(self.generate("2009/10/11").readdir())), 2)
        self.assertEqual(len(list(self.generate("2005/6/30").readdir())[0]), 40)

    def test_days_per_month(self):
        self.assertEqual(self.generate("2017")._days_per_month(2017),
                         [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        self.assertEqual(self.generate("2004")._days_per_month(2004),
                         [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    def test_month_dates(self):
        self.assertEqual(self.generate("2017/1")._month_dates(2017, 1), range(1, 32))

    def test_verify_date_path(self):
        with self.assertRaises(FuseOSError):
            self.generate("foo")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2001/2/3")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2005/06/32")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2004/02/0")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2004/04/2")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2004/01/32")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2004/0/30")._verify_date_path()
        with self.assertRaises(FuseOSError):
            self.generate("2004/00/30")._verify_date_path()
        self.generate("2005")._verify_date_path()
        self.generate("2005/6")._verify_date_path()
        self.generate("2005/06/7")._verify_date_path()
        self.generate("2005/6/01")._verify_date_path()
        self.generate("2005/01/31")._verify_date_path()

    def test_get_symlink_target(self):
        all_commits = list(self.repofs._git.all_commits())
        last_commit = all_commits[0]
        pre_last_commit = all_commits[1]

        with self.assertRaises(FuseOSError):
            self.generate("2005/6/7/commit").get_symlink_target()
        with self.assertRaises(FuseOSError):
            self.generate("2005/6").get_symlink_target()

        recent_commit = '2009/10/11/' + last_commit
        self.assertEqual(self.generate(recent_commit + "/.git-parents/" + pre_last_commit).get_symlink_target(), pre_last_commit)
        link_commit = "2007/01/15/" + list(self.repofs._git.commits_by_date(2007, 1, 15))[0]
        self.assertEqual(self.generate(link_commit + "/link_a").get_symlink_target(), link_commit + "/file_a")



if __name__ == "__main__":
    main()
