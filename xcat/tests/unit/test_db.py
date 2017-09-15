import unittest
import unittest.mock as mock
import xcat.db as db
import xcat.tests.utils as utils


class TestDB(unittest.TestCase):

    @mock.patch('xcat.db.plyvel')
    def setUp(self, mock_plyvel):
        self.db = db.DB()

    def test_init(self):
        self.assertIsInstance(self.db.db, mock.Mock)
        self.assertIsInstance(self.db.preimageDB, mock.Mock)

    @mock.patch('xcat.db.json')
    def test_create_with_dict(self, mock_json):
        test_id = 'test trade id'
        trade_string = 'trade string'
        mock_json.dumps.return_value = trade_string
        test_trade = utils.test_trade

        self.db.create(test_trade, test_id)

        mock_json.dumps.assert_called_with(test_trade)
        self.db.db.put.assert_called_with(
            str.encode(test_id),
            str.encode(trade_string))

    def test_create_with_trade(self):
        pass

    def test_createByFundtx(self):
        pass

    def test_get(self):
        pass

    def test_instantiate(self):
        pass

    def test_save_secret(self):
        pass

    def test_get_secret(self):
        pass

    def test_dump(self):
        pass

    def test_print_entries(self):
        pass
