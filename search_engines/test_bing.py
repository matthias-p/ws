"""Bing unittests"""

import unittest

from search_engines.bing import Bing


class MyTestCase(unittest.TestCase):  # pylint: disable=missing-class-docstring
    def test_10_moons(self):
        """Get 10 urls of moon pictures"""
        bing = Bing("moon", 10)
        self.assertEqual(len(bing.get_img_urls()), 10)

    def test_10_suns(self):
        """Get 10 urls of moon pictures"""
        bing = Bing("sun", 10)
        self.assertEqual(len(bing.get_img_urls()), 10)


if __name__ == '__main__':
    unittest.main()
