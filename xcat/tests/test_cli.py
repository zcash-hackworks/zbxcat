import unittest
import xcat.cli as cli
from xcat.db import DB
from xcat.protocol import Protocol
from xcat.tests.utils import mktrade
from xcat.trades import Trade  # , Contract


class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        self.trade = mktrade()

    def test_exporttrade(self):
        self.__class__.hexstr = cli.exporttrade('test')
        self.assertTrue(int(self.hexstr, 16))

    def test_importtrade(self):
        # trade = cli.importtrade('test', self.__class__.hexstr)
        pass


class CliTest(SimpleTestCase):
    def test_findtrade(self):
        # trade = cli.findtrade('test')
        pass

    def test_newtrade(self):
        trade = cli.newtrade('new', conf='regtest')
        self.assertTrue(isinstance(trade, Trade))

    def test_fundsell(self):
        db = DB()
        protocol = Protocol()

        trade = db.get('new')
        status = cli.seller_check_status(trade)
        print("Trade status: {0}\n".format(status))
        self.assertEqual(status, 'init')

        fund_tx = protocol.fund_sell_contract(trade)
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
