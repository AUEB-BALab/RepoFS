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

from unittest import TestCase, main

from repofs.utils import demux_ref_path, is_metadata_dir, is_metadata_symlink, \
        demux_commits_by_hash_path, demux_commits_by_date_path, metadata_names
from repofs.handlers.ref import BRANCH_REFS, TAG_REFS
from repofs.gitoper import GitOperations

class UtilsTest(TestCase):
    def setUp(self):
        self.gitoper = GitOperations("test_repo")

    def test_demux_ref_path(self):
        branch_refs = self.gitoper.refs(BRANCH_REFS)
        tag_refs = self.gitoper.refs(TAG_REFS)

        self.assertEqual(demux_ref_path("heads/feature/a/dir_a/dir_b", branch_refs), {
                'type': "heads",
                'ref': "heads/feature/a",
                'commit_path': "dir_a/dir_b"
            })
        self.assertEqual(demux_ref_path("heads/master/dir_a/dir_b", branch_refs), {
                'type': "heads",
                'ref': "heads/master",
                'commit_path': "dir_a/dir_b"
            })
        self.assertEqual(demux_ref_path("heads/master", branch_refs), {
                'type': "heads",
                'ref': "heads/master",
                'commit_path': ""
            })
        # demux_ref_path doesn't do validity checks
        self.assertEqual(demux_ref_path("foo/bar/bar/foo", branch_refs), {
                'type': "foo",
                'ref': "foo/bar/bar/foo",
                'commit_path': ""
            })
        self.assertEqual(demux_ref_path("foo", branch_refs), {
                'type': "foo",
                'ref': "foo",
                'commit_path': ""
            })
        self.assertEqual(demux_ref_path("tags/t20091011ca/dir_a/dir_b", tag_refs), {
                'type': "tags",
                'ref': "tags/t20091011ca",
                'commit_path': "dir_a/dir_b"
            })
        self.assertEqual(demux_ref_path("tags/t20091011ca", tag_refs), {
                'type': "tags",
                'ref': "tags/t20091011ca",
                'commit_path': ""
            })
        self.assertEqual(demux_ref_path("tags/tdir/tname/dir_a/dir_b", tag_refs), {
                'type': "tags",
                'ref': "tags/tdir/tname",
                'commit_path': "dir_a/dir_b"
            })

    def test_demux_commits_by_hash_path(self):
        # no hash trees
        self.assertEqual(demux_commits_by_hash_path("", False), {
                'commit': "",
                'commit_path': "",
                'htree_prefix': ""
            })
        self.assertEqual(demux_commits_by_hash_path("aabbcc...", False), {
                'commit': "aabbcc...",
                'commit_path': "",
                'htree_prefix': ""
            })
        self.assertEqual(demux_commits_by_hash_path("aabbcc.../dir_a/file_a", False), {
                'commit': "aabbcc...",
                'commit_path': "dir_a/file_a",
                'htree_prefix': ""
            })

        # hash trees
        self.assertEqual(demux_commits_by_hash_path("aa", True), {
                'commit': "",
                'commit_path': "",
                'htree_prefix': "aa"
            })
        self.assertEqual(demux_commits_by_hash_path("aa/bb", True), {
                'commit': "",
                'commit_path': "",
                'htree_prefix': "aa/bb"
            })
        self.assertEqual(demux_commits_by_hash_path("aa/bb/cc", True), {
                'commit': "",
                'commit_path': "",
                'htree_prefix': "aa/bb/cc"
            })
        self.assertEqual(demux_commits_by_hash_path("aaz/bbz/ccz", True), {
                'commit': "",
                'commit_path': "",
                'htree_prefix': "aaz/bbz/ccz"
            })
        self.assertEqual(demux_commits_by_hash_path("aa/bb/cc/aabbcc...", True), {
                'commit': "aabbcc...",
                'commit_path': "",
                'htree_prefix': "aa/bb/cc"
            })
        self.assertEqual(demux_commits_by_hash_path("aa/bb/cc/aabbcc.../dir_a/file_a", True), {
                'commit': "aabbcc...",
                'commit_path': "dir_a/file_a",
                'htree_prefix': "aa/bb/cc"
            })

    def test_demux_commits_by_date_path(self):
        self.assertEqual(demux_commits_by_date_path(""), {
                'commit': "",
                'commit_path': "",
                'date_path': ""
            })
        self.assertEqual(demux_commits_by_date_path("2007"), {
                'commit': "",
                'commit_path': "",
                'date_path': "2007"
            })
        self.assertEqual(demux_commits_by_date_path("2007/10"), {
                'commit': "",
                'commit_path': "",
                'date_path': "2007/10"
            })
        self.assertEqual(demux_commits_by_date_path("2007/10/20"), {
                'commit': "",
                'commit_path': "",
                'date_path': "2007/10/20"
            })
        self.assertEqual(demux_commits_by_date_path("2007/10/20/commit"), {
                'commit': "commit",
                'commit_path': "",
                'date_path': "2007/10/20"
            })
        self.assertEqual(demux_commits_by_date_path("2007/10/20/commit/dir_a/file_a"), {
                'commit': "commit",
                'commit_path': "dir_a/file_a",
                'date_path': "2007/10/20"
            })

    def test_is_metadata_dir(self):
        self.assertTrue(is_metadata_dir(".git-parents"))
        self.assertFalse(is_metadata_dir(".git-parents2"))

    def test_metadata_names(self):
        self.assertEqual(metadata_names(),
                    [".git-parents", ".git-descendants", ".git-names", ".author", ".author-email"])

    def test_is_metadata_symlink(self):
        self.assertTrue(is_metadata_symlink(".git-parents/commit", ["commit"]))
        self.assertFalse(is_metadata_symlink(".git-parents/commit", ["anothercommit"]))

if __name__ == "__main__":
    main()
