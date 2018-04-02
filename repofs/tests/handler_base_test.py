from unittest import TestCase, main

from repofs.handler_base import HandlerBase

class HandlerBaseTest(TestCase):
    def setUp(self):
        self.handler_base = HandlerBase()

    def test_is_dir(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.is_dir("foobar")

    def test_is_symlink(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.is_symlink("foobar")

    def test_file_contents(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.file_contents("foobar")

    def test_readdir(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.readdir("foobar")

if __name__ == "__main__":
    main()
