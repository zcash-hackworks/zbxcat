import unittest
import unittest.mock as mock
from xcat.bitcoinRPC import bitcoinProxy
import logging


@mock.patch('xcat.bitcoinRPC.bitcoin.rpc')
class TestBitcoinProxy(unittest.TestCase):
    """Test case for the bitcoinProxy class."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    @mock.patch('xcat.bitcoinRPC.bitcoin.SelectParams')
    def test_init_with_testnet(self, mock_SP, mock_rpc):
        """Test bitcoinProxy.__init__"""

        proxy = bitcoinProxy(network='testnet')

        mock_rpc.Proxy.assert_called_with(timeout=900)
        mock_SP.assert_called_with('testnet')
        self.assertIsInstance(proxy, bitcoinProxy)

    @mock.patch('xcat.bitcoinRPC.bitcoin.SelectParams')
    def test_init_with_no_network(self, mock_SP, mock_rpc):
        """Test bitcoinProxy.__init__"""

        proxy = bitcoinProxy()

        mock_rpc.Proxy.assert_called_with(timeout=900)
        mock_SP.assert_called_with('regtest')
        self.assertIsInstance(proxy, bitcoinProxy)

    def test_init_with_invalid(self, mock_rpc):
        """Test bitcoinProxy.__init__"""

        with self.assertRaises(ValueError) as context:
            proxy = bitcoinProxy(network='invalid input')
            self.assertIsNone(proxy)

        self.assertTrue(
            'Allowed networks are regtest, testnet, mainnet.'
            in str(context.exception))

    def test_init_with_invalid_timeout(self, mock_rpc):
        """Test bitcoinProxy.__init__"""

        with self.assertRaises(ValueError) as context:
            proxy = bitcoinProxy(timeout='invalid input')
            self.assertIsNone(proxy)

        self.assertTrue(
            'Timeout should be a positive integer.'
            in str(context.exception))

        with self.assertRaises(ValueError) as context_two:
            proxy = bitcoinProxy(timeout=-381)
            self.assertIsNone(proxy)

        self.assertTrue(
            'Timeout should be a positive integer.'
            in str(context_two.exception))
