"""Google unittests"""

import unittest

from search_engines.google import Google


class MyTestCase(unittest.TestCase):  # pylint: disable=missing-class-docstring
    def test_10_moons(self):
        """Get 10 urls of moon pictures"""
        google = Google("moon", 10)
        self.assertEqual(len(google.get_img_urls()), 10)

    def test_10_suns(self):
        """Get 10 urls of sun pictures"""
        google = Google("sun", 10)
        self.assertEqual(len(google.get_img_urls()), 10)


if __name__ == '__main__':
    unittest.main()
