import unittest
import xcat.cli as cli
from xcat.tests.utils import mktrade

class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        self.trade = mktrade()

    def test_exporttrade(self):
        self.__class__.hexstr = cli.exporttrade('test')
        self.assertTrue(int(self.hexstr, 16))

    def test_importtrade(self):
        trade = cli.importtrade(self.__class__.hexstr, 'test')

class CliTest(SimpleTestCase):
    def test_findtrade(self):
        trade = cli.findtrade('test')

    def test_newtrade(self):
        cli.newtrade('test2')
        cli.checkBuyStatus('test2')
        cli.checkSellStatus('test2')
        cli.checkBuyStatus('test2')

if __name__ == '__main__':
    unittest.main()
