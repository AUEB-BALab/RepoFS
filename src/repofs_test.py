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
        self.second_commit = '/commits-by-date/2006/10/11/' + self.repofs._get_commits_by_date(
            '/commits-by-date/2009/10/11')[0]
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

    def test_is_dir(self):
        self.assertTrue(self.repofs._is_dir('/'))
        self.assertTrue(self.repofs._is_dir('/commits-by-date'))
        self.assertTrue(self.repofs._is_dir('/branches'))
        self.assertTrue(self.repofs._is_dir('/tags'))
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

    def test_target_from_symlink(self):
        self.assertEqual(self.repofs._target_from_symlink('/tags/t20091011ca'),
                         '..' + self.recent_commit + '/')
        self.assertEqual(self.repofs._target_from_symlink('/branches/master'),
                         '..' + self.recent_commit + '/')

if __name__ == "__main__":
    main()
