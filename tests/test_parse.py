import unittest
import time
from ejpcsvparser import parse

class TestParse(unittest.TestCase):

    def setUp(self):
        pass

    def test_dummy(self):
        self.assertEqual(parse.dummy(), None)


if __name__ == '__main__':
    unittest.main()
