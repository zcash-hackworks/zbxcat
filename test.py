import unittest
from api import *
from utils import *
import sys

class TestRefundConditions(unittest.TestCase):
    def setUp(self):
        print("Starting test of redeem conditions...")
        self.htlcTrade = initiate()

    def testSetUp(self):
        # There is a fund_tx and it is not a boolean
        self.assertTrue(len(self.htlcTrade.sellContract.fund_tx) > 20)

    def testRefund(self):
        fund_buyer()
        # zXcat.generate(8)
        zXcat.generate(6)
        redeem_seller()
        zXcat.generate(2)
        bXcat.generate(20)
        redeem_buyer()
        trade = get_trade()
        print("sellContract redeem_tx is:", trade.sellContract.redeem_tx)
        self.assertEqual(trade.sellContract.redeem_tx, False)

class TestRedeem(unittest.TestCase):
    def setUp(self):
        print("Starting test of refund conditions...")
        self.htlcTrade = initiate()

    # Case where both parties act in good faith
    def testRedeem(self):
        fund_buyer()
        zXcat.generate(1)
        redeem_seller()
        zXcat.generate(1)
        bXcat.generate(1)
        redeem_buyer()
        trade = get_trade()
        print("sellContract redeem_tx is:", trade.sellContract.redeem_tx)

if __name__ == '__main__':
    unittest.main()

# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))
