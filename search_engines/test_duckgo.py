"""Duckgo unittests"""

import unittest

from search_engines.duckgo import DuckGo


class MyTestCase(unittest.TestCase):  # pylint: disable=missing-class-docstring
    def test_10_moons(self):
        """Get 10 urls of moon pictures"""
        duck_go = DuckGo("moon", 10)
        self.assertEqual(len(duck_go.get_img_urls()), 10)

    def test_10_suns(self):
        """Get 10 urls of sun pictures"""
        duck_go = DuckGo("sun", 10)
        self.assertEqual(len(duck_go.get_img_urls()), 10)


if __name__ == '__main__':
    unittest.main()
