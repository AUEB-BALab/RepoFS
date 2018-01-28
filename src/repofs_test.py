from unittest import TestCase, main
from os import mkdir, rmdir, errno

from repofs import RepoFS
from fuse import FuseOSError


class RepoFSTestCase(TestCase):
    def setUp(self):
        try:
            mkdir('mnt')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        self.repofs = RepoFS('test_repo', 'mnt', True)
        self.first_commit = '/commits-by-date/2005/6/7/' + self.repofs._get_commits_by_date(
            '/commits-by-date/2005/6/7')[0]
        self.second_commit = '/commits-by-date/2005/6/10/' + self.repofs._get_commits_by_date(
            '/commits-by-date/2005/6/10')[0]
        self.recent_commit = '/commits-by-date/2009/10/11/' + self.repofs._get_commits_by_date(
            '/commits-by-date/2009/10/11')[0]

    def test_days_per_month(self):
        self.assertEqual(self.repofs._days_per_month(2017),
                         [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        self.assertEqual(self.repofs._days_per_month(2004),
                         [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    def test_month_dates(self):
        self.assertEqual(self.repofs._month_dates(2017, 1), range(1, 32))

    def test_verify_date_path(self):
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path(['foo'])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2001, 2, 3])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2005, 6, 32])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2004, 2, 0])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2004, 2, 30])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2004, 1, 32])
        with self.assertRaises(FuseOSError):
            self.repofs._verify_date_path([2004, 0, 30])
        self.repofs._verify_date_path([2005])
        self.repofs._verify_date_path([2005, 6])
        self.repofs._verify_date_path([2005, 6, 7])
        self.repofs._verify_date_path([2005, 6, 1])
        self.repofs._verify_date_path([2005, 1, 31])

    def test_verify_commits_parents(self):
        first = self.first_commit.split("/")[-1]
        second = self.second_commit.split("/")[-1]
        self.assertEqual(self.repofs._get_metadata_folder(second, ".git-parents"), [first])

    def test_verify_commits_by_date(self):
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date')), 5)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/')), 5)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005')), 12)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6')), 30)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/7')), 1)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/6')), 0)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/8')), 0)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/29')), 0)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/30')), 1)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/7/1')), 2)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2009/10/11')), 2)
        self.assertEqual(len(self.repofs._get_commits_by_date('/commits-by-date/2005/6/30')[0]), 40)

    def test_verify_commits_by_hash(self):
        self.assertGreater(len(self.repofs._get_commits_by_hash('/commits-by-hash')), 3)
        self.assertGreater(len(self.repofs._get_commits_by_hash('/commits-by-hash/')), 3)
        self.assertEqual(len(self.repofs._get_commits_by_hash('/commits-by-hash/')[0]), 40)

    def test_path_to_refs(self):
        self.assertEqual(self.repofs._path_to_refs('/branches/heads/foo'),
                         ['heads', 'foo'])
        self.assertEqual(self.repofs._path_to_refs('/tags/tagname'),
                         ['tags', 'tagname'])

    def test_git_path(self):
        self.assertEqual(self.repofs._git_path(
            '/commits-by-date/2017/12/28/ed34f8.../src/foo'), 'src/foo')
        self.assertEqual(self.repofs._git_path(
            '/commits-by-date/2017/12/28/ed34f8.../README'), 'README')
        self.assertEqual(self.repofs._git_path(
            '/commits-by-date/2017/12/28/ed34f8...'), '')

    def test_verify_commit_files(self):
        entries = self.repofs._get_commits_by_date(self.recent_commit)
        self.assertTrue(entries, 'file_a' in entries)

    def test_readdir(self):
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/', None)), 6)
        self.assertTrue('tags' in self.repofs.readdir('/', None))
        self.assertTrue('branches' in self.repofs.readdir('/', None))
        self.assertTrue('commits-by-date' in self.repofs.readdir('/', None))
        self.assertTrue('commits-by-hash' in self.repofs.readdir('/', None))

    def test_readdir_branches(self):
        self.assertTrue('heads' in self.repofs.readdir('/branches', None))
        with self.assertRaises(FuseOSError):
            self.repofs.readdir('/branches/branchpartfoo/bar', None).next()
        self.assertTrue('b20050701' in self.repofs.readdir('/branches/heads', None))
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/branches/heads', None)), 6)
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/branches/heads/private', None)), 3)
        self.assertTrue('a' in self.repofs.readdir('/branches/heads/feature', None))
        self.assertTrue('b' in self.repofs.readdir('/branches/heads/private/john', None))
        self.assertTrue('c' in self.repofs.readdir('/branches/heads/private/john', None))
        with self.assertRaises(FuseOSError):
            self.repofs.readdir('/branches/heads/feature/xyzzy', None).next()

    def test_readdir_tags(self):
        self.assertTrue('t20091011ca' in self.repofs.readdir('/tags', None))
        self.assertTrue('tdir' in self.repofs.readdir('/tags', None))
        with self.assertRaises(FuseOSError):
            self.repofs.readdir('/tags/tagpartfoo/bar', None).next()
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/tags', None)), 8)
        self.assertEqual(sum(1 for _ in self.repofs.readdir('/tags/tdir', None)), 3)
        self.assertTrue('tname' in self.repofs.readdir('/tags/tdir', None))
        with self.assertRaises(FuseOSError):
            self.repofs.readdir('/tags/tdir/xyzzy', None).next()

    def test_is_dir(self):
        self.assertTrue(self.repofs._is_dir('/'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date'))
        self.assertTrue(self.repofs._is_dir('/branches'))
        self.assertTrue(self.repofs._is_dir('/branches/heads'))
        self.assertTrue(self.repofs._is_dir('/branches/heads/feature'))
        self.assertFalse(self.repofs._is_dir('/branches/heads/feature/a'))
        self.assertTrue(self.repofs._is_dir('/tags'))
        self.assertTrue(self.repofs._is_dir('/tags/tdir'))
        self.assertFalse(self.repofs._is_dir('/tags/tdir/tname'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date/2005'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date/2005/7'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date/2005/7/1'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date/2005/6/7'))
        self.assertTrue(self.repofs._is_dir(self.recent_commit))
        self.assertTrue(self.repofs._is_dir(self.recent_commit + '/dir_a'))
        self.assertTrue(self.repofs._is_dir(self.recent_commit + '/dir_a/dir_b'))
        self.assertTrue(self.repofs._is_dir(self.recent_commit + '/dir_a/dir_b/dir_c'))
        self.assertFalse(self.repofs._is_dir(self.recent_commit + '/file_a'))
        self.assertFalse(self.repofs._is_dir(self.recent_commit + '/.git-log'))
        self.assertFalse(self.repofs._is_dir(self.recent_commit + '/dir_a/file_aa'))

    def test_is_branch_ref(self):
        br = self.repofs._branch_refs
        self.assertTrue(self.repofs._is_ref('/branches/heads/master', br))
        self.assertTrue(self.repofs._is_ref('/branches/heads/feature/a', br))
        self.assertFalse(self.repofs._is_ref('/branches/heads/feature/', br))
        self.assertFalse(self.repofs._is_ref('/branches/heads/feature/b', br))
        self.assertFalse(self.repofs._is_ref('/branches/heads/feature', br))
        self.assertFalse(self.repofs._is_ref('/branches/heads/private/john', br))
        self.assertFalse(self.repofs._is_ref('/branches/heads/private/', br))
        self.assertTrue(self.repofs._is_ref('/branches/heads/private/john/b', br))
    def test_is_tag_ref(self):
        tr = self.repofs._tag_refs
        self.assertTrue(self.repofs._is_ref('/tags/t20091011ca', tr))
        self.assertTrue(self.repofs._is_ref('/tags/tdir/tname', tr))
        self.assertFalse(self.repofs._is_ref('/tags/tdir', tr))
        self.assertFalse(self.repofs._is_ref('/tags/tdir/', tr))

    def test_is_symlink(self):
        self.assertTrue(self.repofs._is_symlink('/tags/t20091011ca'))
        self.assertFalse(self.repofs._is_symlink('/tags/tdir'))
        self.assertTrue(self.repofs._is_symlink('/tags/tdir/tname'))
        self.assertTrue(self.repofs._is_symlink('/branches/heads/master'))
        self.assertFalse(self.repofs._is_symlink('/branches/heads/feature'))

    def test_target_from_symlink(self):
        self.assertEqual(self.repofs._target_from_symlink('/tags/t20091011ca'),
                         '..' + self.recent_commit + '/')
        self.assertEqual(self.repofs._target_from_symlink('/branches/heads/master'),
                         '../..' + self.recent_commit + '/')
        self.assertEqual(self.repofs._target_from_symlink('/branches/master'),
                         '..' + self.recent_commit + '/')
        self.assertEqual(self.repofs._target_from_symlink(
                self.second_commit + '/.git-parents/' + self.first_commit.split("/")[-1]),
                self.repofs.mount + '/commits-by-hash/' + self.first_commit.split("/")[-1] + "/")
        self.assertEqual(self.repofs._target_from_symlink(
                '/commits-by-hash/' + self.second_commit.split("/")[-1] + '/.git-parents/' + self.first_commit.split("/")[-1]),
                self.repofs.mount + '/commits-by-hash/' + self.first_commit.split("/")[-1] + "/")

if __name__ == "__main__":
    main()
