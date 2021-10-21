import unittest

from search_engines.google import Google


class MyTestCase(unittest.TestCase):
    def test_something(self):
        google = Google("house", 10)


if __name__ == '__main__':
    unittest.main()
