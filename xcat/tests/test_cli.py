import unittest
import unittest.mock as mock
import xcat.cli as cli
# from xcat.tests.utils import test_trade
# from xcat.trades import Trade


class TestCLI(unittest.TestCase):

    def test_save_state(self):
        pass

    def test_checkSellStatus(self):
        pass

    def test_buyer_check_status(self):
        pass

    def test_seller_check_status(self):
        pass

    def test_checkBuyStatus(self):
        pass

    def test_importtrade(self):
        pass

    def test_wormhole_importtrade(self):
        pass

    def test_exporttrade(self):
        pass

    def test_findtrade(self):
        pass

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_test(self, mock_protocol):
        mock_protocol().is_myaddr.return_value = True

        test_contract = mock.MagicMock()
        test_contract.initiator = 'test initiator'
        test_contract.fulfiller = 'test fulfiller'

        res = cli.find_role(test_contract)

        self.assertEqual(res, 'test')

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_initiator(self, mock_protocol):
        pass

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_fulfiller(self, mock_protocol):
        pass

    def test_checktrade(self):
        pass

    def test_newtrade(self):
        pass

    def test_listtrades(self):
        pass

    def test_fundsell(self):
        pass

    def test_fundbuy(self):
        pass

    def test_seller_redeem(self):
        pass

    def test_buyer_redeem(self):
        pass


if __name__ == '__main__':
    unittest.main()
