from unittest import TestCase, main

from utils import demux_ref_path, is_metadata_dir, is_metadata_symlink, \
        demux_commits_by_hash_path
from ref import BRANCH_REFS, TAG_REFS
from gitoper import GitOperations

class UtilsTest(TestCase):
    def setUp(self):
        self.gitoper = GitOperations("test_repo", True)

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

    def test_is_metadata_dir(self):
        self.assertTrue(is_metadata_dir(".git-parents"))
        self.assertFalse(is_metadata_dir(".git-parents2"))

    def test_is_metadata_symlink(self):
        self.assertTrue(is_metadata_symlink(".git-parents/commit", ["commit"]))
        self.assertFalse(is_metadata_symlink(".git-parents/commit", ["anothercommit"]))

if __name__ == "__main__":
    main()
