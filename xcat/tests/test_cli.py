import unittest
import xcat.cli as cli
import xcat.db as db
from xcat.tests.utils import mktrade
from xcat.trades import Trade, Contract

class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        self.trade = mktrade()

    def test_exporttrade(self):
        self.__class__.hexstr = cli.exporttrade('test')
        self.assertTrue(int(self.hexstr, 16))

    def test_importtrade(self):
        trade = cli.importtrade('test', self.__class__.hexstr)

class CliTest(SimpleTestCase):
    def test_findtrade(self):
        trade = cli.findtrade('test')

    def test_newtrade(self):
        trade = cli.newtrade('new', conf='regtest')
        self.assertTrue(isinstance(trade, Trade))

    def test_fundsell(self):
        trade = db.get('new')
        status = cli.seller_check_status(trade)
        print("Trade status: {0}\n".format(status))
        self.assertEqual(status, 'init')
        fund_tx = cli.fund_sell_contract(trade)
        print("Sent fund_tx", fund_tx)

    # def test_fundbuy(self):
    #     trade = db.get('new')
    #     status = cli.buyer_check_status(trade)
    #     self.assertEqual(status, 'sellerFunded')
    #     fund_tx = cli.fund_contract(trade.buy)
    #
    # def test_seller_redeem(self):
    #     trade = db.get('new')
    #     status = cli.seller_check_status(trade)
    #     self.assertEqual(status, 'buyerFunded')
    #
    # def test_buyer_redeem(self):
    #     trade = db.get('new')
    #     status = cli.buyer_check_status(trade)
    #     self.assertEqual(status, 'sellerFunded')

if __name__ == '__main__':
    unittest.main()
