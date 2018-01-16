from unittest import TestCase, main
from gitoper import GitOperations


class GitOperationsTestCase(TestCase):
    def setUp(self):
        self.go = GitOperations('test_repo', True)

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

if __name__ == "__main__":
    main()
