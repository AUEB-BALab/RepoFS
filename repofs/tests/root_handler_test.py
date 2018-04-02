from unittest import TestCase, main
from repofs.handlers.root import RootHandler

class RootHandlerTest(TestCase):
    def test_handler(self):
        handler = RootHandler()
        self.assertTrue(handler.is_dir())
        self.assertEqual(handler.readdir(), ['commits-by-date', 'commits-by-hash', 'branches', 'tags'])

if __name__ == "__main__":
    main()
