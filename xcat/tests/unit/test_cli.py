import unittest
import unittest.mock as mock
import xcat.cli as cli
# from xcat.tests.utils import test_trade
# from xcat.trades import Trade


class TestCLI(unittest.TestCase):

    @mock.patch('xcat.cli.DB')
    @mock.patch('xcat.cli.utils')
    def test_save_state(self, mock_utils, mock_db):
        cli.save_state('fake_trade', 'fake_id')

        mock_utils.save.assert_called_with('fake_trade')
        mock_db.return_value.create.assert_called_with('fake_trade', 'fake_id')

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
        mock_protocol().is_myaddr = lambda k: k == 'me'

        test_contract = mock.MagicMock()
        test_contract.initiator = 'me'
        test_contract.fulfiller = 'me'

        res = cli.find_role(test_contract)

        self.assertEqual(res, 'test')

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_initiator(self, mock_protocol):
        mock_protocol().is_myaddr = lambda k: k == 'me'

        test_contract = mock.MagicMock()
        test_contract.initiator = 'me'
        test_contract.fulfiller = 'you'

        res = cli.find_role(test_contract)

        self.assertEqual(res, 'initiator')

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_fulfiller(self, mock_protocol):
        mock_protocol().is_myaddr = lambda k: k == 'me'

        test_contract = mock.MagicMock()
        test_contract.initiator = 'you'
        test_contract.fulfiller = 'me'

        res = cli.find_role(test_contract)

        self.assertEqual(res, 'fulfiller')

    @mock.patch('xcat.cli.Protocol')
    def test_find_role_error(self, mock_protocol):
        mock_protocol().is_myaddr = lambda k: k == 'me'

        test_contract = mock.MagicMock()
        test_contract.initiator = 'you'
        test_contract.fulfiller = 'you'

        with self.assertRaises(ValueError) as context:
            cli.find_role(test_contract)

        self.assertTrue(
            'You are not a participant in this contract.'
            in str(context.exception))

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
