import unittest
import unittest.mock as mock
from xcat.zcashRPC import zcashProxy
import logging


@mock.patch('xcat.zcashRPC.zcash.rpc')
class TestBitcoinProxy(unittest.TestCase):
    """Test case for the zcashProxy class."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    @mock.patch('xcat.zcashRPC.zcash.SelectParams')
    def test_init_with_testnet(self, mock_SP, mock_rpc):
        """Test zcashProxy.__init__"""

        proxy = zcashProxy(network='testnet')

        mock_rpc.Proxy.assert_called_with(timeout=900)
        mock_SP.assert_called_with('testnet')
        self.assertIsInstance(proxy, zcashProxy)

    @mock.patch('xcat.zcashRPC.zcash.SelectParams')
    def test_init_with_no_network(self, mock_SP, mock_rpc):
        """Test zcashProxy.__init__"""

        proxy = zcashProxy()

        mock_rpc.Proxy.assert_called_with(timeout=900)
        mock_SP.assert_called_with('regtest')
        self.assertIsInstance(proxy, zcashProxy)

    def test_init_with_invalid(self, mock_rpc):
        """Test zcashProxy.__init__"""

        with self.assertRaises(ValueError) as context:
            proxy = zcashProxy(network='invalid input')
            self.assertIsNone(proxy)

        self.assertTrue(
            'Allowed networks are regtest, testnet, mainnet.'
            in str(context.exception))

        with self.assertRaises(ValueError) as context_two:
            proxy = zcashProxy(network=819.3)
            self.assertIsNone(proxy)

        self.assertTrue(
            'Allowed networks are regtest, testnet, mainnet.'
            in str(context_two.exception))

    def test_init_with_invalid_timeout(self, mock_rpc):
        """Test zcashProxy.__init__"""

        with self.assertRaises(ValueError) as context:
            proxy = zcashProxy(timeout='invalid input')
            self.assertIsNone(proxy)

        self.assertTrue(
            'Timeout should be a positive integer.'
            in str(context.exception))

        with self.assertRaises(ValueError) as context_two:
            proxy = zcashProxy(timeout=-381)
            self.assertIsNone(proxy)

        self.assertTrue(
            'Timeout should be a positive integer.'
            in str(context_two.exception))

    def test_validateaddress(self, mock_rpc):
        pass

    def test_find_secret(self, mock_rpc):
        pass

    def test_parse_secret(self, mock_rpc):
        pass

    def test_get_keys(self, mock_rpc):
        pass

    def test_privkey(self, mock_rpc):
        pass

    def test_hashtimelockcontract(self, mock_rpc):
        pass

    def test_fund_htlc(self, mock_rpc):
        pass

    def test_check_funds(self, mock_rpc):
        pass

    def test_get_fund_status(self, mock_rpc):
        pass

    def test_search_p2sh(self, mock_rpc):
        pass

    def test_get_tx_details(self, mock_rpc):
        pass

    def test_redeem_contract(self, mock_rpc):
        pass

    def test_redeem(self, mock_rpc):
        pass

    def test_refund(self, mock_rpc):
        pass

    def test_parse_script(self, mock_rpc):
        pass

    def test_find_redeemblocknum(self, mock_rpc):
        pass

    def test_find_redeemAddr(self, mock_rpc):
        pass

    def test_find_refundAddr(self, mock_rpc):
        pass

    def test_find_transaction_to_address(self, mock_rpc):
        pass

    def test_new_bitcoin_addr(self, mock_rpc):
        pass

    def test_generate(self, mock_rpc):
        pass
