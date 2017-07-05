import unittest
from api import *
from utils import *

class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        print("Starting testing 123")
        self.htlcTrade = initiate()

class TestRedeem(SimpleTestCase):
    def testfundBuyer(self):
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

if __name__ == '__main__':
    unittest.main()

# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))
