import unittest
import time
from ejpcsvparser import parse

class TestParse(unittest.TestCase):

    def setUp(self):
        pass

    def test_build_article(self):
        article_id = 21598
        article, error_count, error_messages = parse.build_article(article_id)
        self.assertIsNotNone(article)


if __name__ == '__main__':
    unittest.main()
