import os
import errno

from unittest import TestCase, main
from fuse import FuseOSError

from commit_hash import CommitHashHandler
from repofs import RepoFS
import utils


class CommitHashHandlerTest(TestCase):
    def setUp(self):
        self.mount = 'mnt'
        try:
            os.mkdir(self.mount)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        self.repofs_htree = RepoFS('test_repo', self.mount, True, False, True)

    def generate(self, path, hash_trees):
        oper = self.repofs_htree._git
        return CommitHashHandler(path, oper, hash_trees)

    def to_hash_path(self, commit):
        return os.path.join(commit[:2], commit[2:4], commit[4:6])

    def test_is_dir(self):
        last_commit = list(self.repofs_htree._git.all_commits())[0]
        # no hash trees
        self.assertTrue(self.generate("", False).is_dir())
        self.assertTrue(self.generate(last_commit, False).is_dir())
        self.assertTrue(self.generate(last_commit + "/dir_a", False).is_dir())
        self.assertTrue(self.generate(last_commit + "/.git-parents", False).is_dir())
        self.assertFalse(self.generate(last_commit + "/dir_a/file_aa", False).is_dir())
        self.assertFalse(self.generate(last_commit + "/file_a", False).is_dir())
        with self.assertRaises(FuseOSError):
            self.generate("aa", False).is_dir()

        # hash trees
        self.assertTrue(self.generate("", True).is_dir())
        self.assertTrue(self.generate("aa", True).is_dir())
        self.assertTrue(self.generate("aa/bb", True).is_dir())
        self.assertTrue(self.generate("aa/bb/cc", True).is_dir())
        self.assertTrue(self.generate("aa/bb/cc", True).is_dir())
        self.assertTrue(self.generate(self.to_hash_path(last_commit) + "/" + last_commit, True).is_dir())
        with self.assertRaises(FuseOSError):
            self.generate(last_commit, True).is_dir()

        with self.assertRaises(FuseOSError):
            self.generate("zz", True).is_dir()

    def test_is_symlink(self):
        last_commit = list(self.repofs_htree._git.all_commits())[0]
        pre_last_commit = list(self.repofs_htree._git.all_commits())[1]
        # no hash trees
        self.assertFalse(self.generate("", False).is_symlink())
        self.assertFalse(self.generate(last_commit, False).is_symlink())
        self.assertFalse(self.generate(last_commit + "/.git-parents", False).is_symlink())
        self.assertTrue(self.generate(last_commit + "/.git-parents/" + pre_last_commit, False).is_symlink())

        # hash trees
        self.assertFalse(self.generate("", True).is_symlink())
        self.assertFalse(self.generate("aa", True).is_symlink())
        self.assertFalse(self.generate("aa/bb", True).is_symlink())
        self.assertFalse(self.generate("aa/bb/cc", True).is_symlink())
        self.assertFalse(self.generate(self.to_hash_path(last_commit) + "/" + last_commit, True).is_symlink())
        self.assertFalse(self.generate(self.to_hash_path(last_commit) + "/" + last_commit + "/.git-parents", True).is_symlink())
        self.assertTrue(self.generate(self.to_hash_path(last_commit) + "/" + last_commit + "/.git-parents/" + pre_last_commit, True).is_symlink())

    def test_readdir(self):
        all_commits = list(self.repofs_htree._git.all_commits())
        last_commit = all_commits[0]
        contents_of_last = self.repofs_htree._git.directory_contents(last_commit, "")
        contents_of_last_dira = self.repofs_htree._git.directory_contents(last_commit, "dir_a")

        self.assertGreater(len(list(self.generate("", False).readdir())), 1)
        self.assertEqual(len(list(self.generate("", False).readdir())), 8)
        self.assertEqual(list(self.generate("", False).readdir()), all_commits)
        self.assertEqual(list(self.generate(last_commit, False).readdir()), list(contents_of_last) + utils.metadata_names())
        self.assertEqual(list(self.generate(last_commit + "/dir_a", False).readdir()), list(contents_of_last_dira))

        # hash trees
        self.assertEqual(len(list(self.generate("", True).readdir())), 256)
        self.assertEqual(len(list(self.generate("aa", True).readdir())), 256)
        self.assertEqual(len(list(self.generate("aa/bb", True).readdir())), 256)
        self.assertGreaterEqual(len(list(self.generate(self.to_hash_path(last_commit), True).readdir())), 1)
        self.assertEqual(self.generate(self.to_hash_path(last_commit), True).readdir().next(), last_commit)
        self.assertEqual(self.generate(self.to_hash_path(last_commit) + "/" + last_commit, True).readdir(), contents_of_last + utils.metadata_names())
        self.assertEqual(self.generate(self.to_hash_path(last_commit) + "/" + last_commit + "/dir_a", True).readdir(), list(contents_of_last_dira))


if __name__ == "__main__":
    main()
