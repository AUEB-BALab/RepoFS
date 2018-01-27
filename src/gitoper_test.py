from unittest import TestCase, main
from gitoper import GitOperations


class GitOperationsTestCase(TestCase):
    def setUp(self):
        self.go = GitOperations('test_repo', True)
        self.master_hash = self.go.last_commit_of_branch("master").split("/")[-1]

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
        self.assertGreater(len(self.go.all_commits()), 3)

    def test_file_size(self):
        self.assertTrue(self.go.file_size(self.master_hash, "file_a") > 0)
        self.assertEqual(self.go.file_size(self.master_hash, "file_b"), 0)
        self.assertEqual(self.go.file_size(self.master_hash, "file_z"), 0)

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
        self.assertEqual(self.go.directory_contents(self.master_hash, "dir_z"), [])

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
        self.assertEqual(self.go._get_tree(self.master_hash, ""), [("dir_a", "tree")] + [("file_" + c, "blob") for c in "abcdr"])

    def test_cache_trees(self):
        self.go._cache_tree(self.master_hash, "dir_a")

        self.assertEqual(self.go._trees[self.master_hash], set(["dir_a/dir_b"]))
        self.assertEqual(self.go._trees_filled[self.master_hash], set(["dir_a"]))

if __name__ == "__main__":
    main()
