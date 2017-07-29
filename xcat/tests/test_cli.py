import unittest
import xcat.cli as cli
from xcat.tests.utils import mktrade

class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        self.trade = mktrade()
        self.hexstr = cli.exporttrade('test')

    def test_exporttrade(self):
        self.assertTrue(int(self.hexstr, 16))

class CliTest(SimpleTestCase):
    def test_importtrade(self):
        trade = cli.importtrade(self.hexstr, 'test')

    def test_newtrade(self):
        cli.newtrade('test2')

if __name__ == '__main__':
    unittest.main()
