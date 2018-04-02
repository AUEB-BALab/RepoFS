import os
import errno

from unittest import TestCase, main
from fuse import FuseOSError

from repofs.handlers.ref import RefHandler, BRANCH_REFS, TAG_REFS
from repofs.repofs import RepoFS

class RefHandlerTest(TestCase):
    def setUp(self):
        self.br_refs = BRANCH_REFS
        self.t_refs = TAG_REFS
        self.mount = "mnt"
        try:
            os.mkdir(self.mount)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        self.repofs_nosym = RepoFS('test_repo', self.mount, False, True, True)
        rcommit = self.repofs_nosym._git.commits_by_date(2009, 10, 11)[0]
        self.recent_commit_by_hash = '/commits-by-hash/' + rcommit

    def generate(self, path, refs, no_ref_sym):
        oper = self.repofs_nosym._git
        return RefHandler(path, oper, refs, no_ref_sym)

    def test_has_attr(self):
        handler = self.generate("heads/master", self.br_refs, False)
        self.assertTrue(hasattr(handler, "path"))
        self.assertTrue(hasattr(handler, "oper"))
        self.assertTrue(hasattr(handler, "refs"))
        self.assertTrue(hasattr(handler, "no_ref_symlinks"))
        self.assertEqual(handler.path, "heads/master")
        self.assertEqual(handler.oper, self.repofs_nosym._git)
        self.assertEqual(handler.refs, self.repofs_nosym._git.refs(self.br_refs))
        self.assertEqual(handler.no_ref_symlinks, False)

        handler = self.generate("t20091011ca", self.t_refs, False)
        self.assertEqual(handler.path, "t20091011ca")
        self.assertEqual(handler.refs, self.repofs_nosym._git.refs(self.t_refs))

    def test_is_dir(self):
        # branches
        self.assertTrue(self.generate("", self.br_refs, False).is_dir())
        self.assertTrue(self.generate("heads", self.br_refs, False).is_dir())
        self.assertTrue(self.generate("heads/feature", self.br_refs, False).is_dir())
        self.assertFalse(self.generate("heads/feature/a", self.br_refs, False).is_dir())

        # no ref symlinks
        self.assertTrue(self.generate("", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads/feature/a", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads/master", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads/feature", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads/feature/a", self.br_refs, True).is_dir())
        self.assertFalse(self.generate("foo", self.br_refs, True).is_dir())
        self.assertFalse(self.generate("heads/foo", self.br_refs, True).is_dir())
        self.assertTrue(self.generate("heads/master/.git-parents", self.br_refs, True).is_dir())

        # tags
        self.assertTrue(self.generate("", self.t_refs, False).is_dir())
        self.assertTrue(self.generate("tags/tdir", self.t_refs, False).is_dir())
        self.assertFalse(self.generate("tags/tdir/tname", self.t_refs, False).is_dir())

        # no ref symlinks
        self.assertTrue(self.generate("tags", self.t_refs, True).is_dir())
        self.assertTrue(self.generate("tags/tdir", self.t_refs, True).is_dir())
        self.assertTrue(self.generate("tags/tdir/tname", self.t_refs, True).is_dir())
        self.assertTrue(self.generate("tags/t20091011ca", self.t_refs, True).is_dir())
        self.assertFalse(self.generate("tags/foo", self.t_refs, True).is_dir())
        self.assertFalse(self.generate("foo", self.t_refs, True).is_dir())
        self.assertTrue(self.generate("tags/tdir/tname/.git-parents", self.t_refs, True).is_dir())

    def test_is_full_ref(self):
        # tags
        self.assertTrue(self.generate("tags/t20091011ca", self.t_refs, False)._is_full_ref())
        self.assertTrue(self.generate("tags/tdir/tname", self.t_refs, False)._is_full_ref())
        self.assertFalse(self.generate("tags/tdir", self.t_refs, False)._is_full_ref())
        self.assertFalse(self.generate("tags/tdir/", self.t_refs, False)._is_full_ref())

        # no ref symlink
        self.assertTrue(self.generate("tags/tdir/tname", self.t_refs, True)._is_full_ref())
        self.assertTrue(self.generate("tags/t20091011ca", self.t_refs, True)._is_full_ref())
        self.assertFalse(self.generate("tags", self.t_refs, True)._is_full_ref())
        self.assertFalse(self.generate("tags/tdir", self.t_refs, True)._is_full_ref())
        self.assertFalse(self.generate("tags/t20091011cafoo", self.t_refs, True)._is_full_ref())
        self.assertFalse(self.generate("tags/tdir/tnamefoo", self.t_refs, True)._is_full_ref())
        self.assertTrue(self.generate("tags/tdir/tname/foo/bar", self.t_refs, True)._is_full_ref())

        # branches
        self.assertTrue(self.generate("heads/master", self.br_refs, False)._is_full_ref())
        self.assertTrue(self.generate("heads/feature/a", self.br_refs, False)._is_full_ref())
        self.assertFalse(self.generate("heads/feature/", self.br_refs, False)._is_full_ref())
        self.assertFalse(self.generate("heads/feature/b", self.br_refs, False)._is_full_ref())
        self.assertFalse(self.generate("heads/feature", self.br_refs, False)._is_full_ref())
        self.assertFalse(self.generate("heads/private/john", self.br_refs, False)._is_full_ref())
        self.assertFalse(self.generate("heads/private/", self.br_refs, False)._is_full_ref())
        self.assertTrue(self.generate("heads/private/john/b", self.br_refs, False)._is_full_ref())

        # no ref symlink
        self.assertTrue(self.generate("heads/master", self.br_refs, True)._is_full_ref())
        self.assertTrue(self.generate("heads/feature/a", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("heads", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("remotes", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("heads/masterfoo", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("heads/feature", self.br_refs, True)._is_full_ref())
        self.assertFalse(self.generate("heads/private", self.br_refs, True)._is_full_ref())
        self.assertTrue(self.generate("heads/master/foo/bar", self.br_refs, True)._is_full_ref())


    def test_is_symlink(self):
        parentcommit = list(self.repofs_nosym.readdir("/branches/heads/master/.git-parents", None))[-1]
        # tags
        self.assertTrue(self.generate("tags/t20091011ca", self.t_refs, False).is_symlink())
        self.assertFalse(self.generate("tags/tdir", self.t_refs, False).is_symlink())
        self.assertTrue(self.generate("tags/tdir/tname", self.t_refs, False).is_symlink())
        # no ref symlink
        self.assertTrue(self.generate("tags/t20091011ca/.git-parents/" + parentcommit, self.t_refs, True).is_symlink())

        # branches
        self.assertTrue(self.generate("heads/master", self.br_refs, False).is_symlink())
        self.assertFalse(self.generate("heads/feature", self.br_refs, False).is_symlink())
        # no ref symlink
        self.assertFalse(self.generate("heads/master", self.br_refs, True).is_symlink())
        self.assertTrue(self.generate("heads/master/.git-parents/" + parentcommit, self.br_refs, True).is_symlink())

    def test_commit_from_path(self):
        commit = self.recent_commit_by_hash.split("/")[-1]
        self.assertEqual(self.generate("heads/master", self.br_refs, True).get_commit(), commit)
        self.assertEqual(self.generate("heads/feature/a", self.br_refs, True).get_commit(), self.repofs_nosym._git.commit_of_ref("heads/feature/a"))
        self.assertEqual(self.generate("heads/feature", self.br_refs, True).get_commit(), "")
        self.assertEqual(self.generate("tags/t20091011ca", self.t_refs, True).get_commit(), commit)
        self.assertEqual(self.generate("tags/tdir/tname", self.t_refs, True).get_commit(), self.repofs_nosym._git.commit_of_ref("tags/tdir/tname"))
        self.assertEqual(self.generate("tags/tdir", self.t_refs, True).get_commit(), "")

    def test_file_contents(self):
        self.assertEqual(self.generate("heads/master/file_a", self.br_refs, True).file_contents(),
                self.repofs_nosym._git.file_contents(self.repofs_nosym._git.commit_of_ref("heads/master"), "file_a"))
        self.assertEqual(self.generate("heads/master/dir_a/file_aa", self.br_refs, True).file_contents(),
                self.repofs_nosym._git.file_contents(self.repofs_nosym._git.commit_of_ref("heads/master"), "dir_a/file_aa"))

    def test_readdir(self):
        # branches
        self.assertTrue('heads' in self.generate("", self.br_refs, False).readdir())
        with self.assertRaises(FuseOSError):
            self.generate("branchpartfoo/bar", self.br_refs, False).readdir()
        self.assertTrue('b20050701' in self.generate("heads", self.br_refs, False).readdir())
        self.assertEqual(sum(1 for _ in self.generate("heads", self.br_refs, False).readdir()), 5)
        self.assertEqual(sum(1 for _ in self.generate("heads/private", self.br_refs, False).readdir()), 1)
        self.assertTrue('a' in self.generate("heads/feature", self.br_refs, False).readdir())
        self.assertTrue('b' in self.generate("heads/private/john", self.br_refs, False).readdir())
        self.assertTrue('c' in self.generate("heads/private/john", self.br_refs, False).readdir())
        with self.assertRaises(FuseOSError):
            self.generate("heads/feature/xyzzy", self.br_refs, False).readdir()

        # no ref symlinks
        with self.assertRaises(FuseOSError):
            self.generate("branchpartfoo/bar", self.br_refs, True).readdir()
        self.assertTrue('heads' in self.generate("", self.br_refs, True).readdir())
        self.assertTrue('b20050701' in self.generate("heads", self.br_refs, True).readdir())
        self.assertEqual(sum(1 for _ in self.generate("heads/feature/a/.git-parents", self.br_refs, True).readdir()), 1)

        # tags
        self.assertTrue('t20091011ca' in self.generate("tags", self.t_refs, False).readdir())
        self.assertTrue('tdir' in self.generate("tags", self.t_refs, False).readdir())
        with self.assertRaises(FuseOSError):
            self.generate("tags/tagpartfoo/bar", self.t_refs, False).readdir()
        self.assertEqual(sum(1 for _ in self.generate("tags", self.t_refs, False).readdir()), 7)
        self.assertEqual(sum(1 for _ in self.generate("tags/tdir", self.t_refs, False).readdir()), 1)
        self.assertTrue('tname' in self.generate("tags/tdir", self.t_refs, False).readdir())
        with self.assertRaises(FuseOSError):
            self.generate("tags/tdir/xyzzy", self.t_refs, False).readdir()

        # no ref symlinks
        self.assertTrue('t20091011ca' in self.generate("tags", self.t_refs, True).readdir())
        self.assertTrue('tname' in self.generate("tags/tdir", self.t_refs, True).readdir())
        self.assertEqual(sum(1 for _ in self.generate("tags", self.t_refs, True).readdir()), 7)
        self.assertEqual(sum(1 for _ in self.generate("tags/tdir", self.t_refs, True).readdir()), 1)
        with self.assertRaises(FuseOSError):
            self.generate("tags/tdir/xyzzy", self.t_refs, True).readdir()

if __name__ == "__main__":
    main()
