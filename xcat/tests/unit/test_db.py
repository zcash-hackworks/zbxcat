import unittest
import unittest.mock as mock
import json
import xcat.db as db
import xcat.tests.utils as utils


class TestDB(unittest.TestCase):

    @mock.patch('xcat.db.plyvel')
    def setUp(self, mock_plyvel):
        self.db = db.DB()

    def test_init(self):
        self.assertIsInstance(self.db.db, mock.Mock)
        self.assertIsInstance(self.db.preimageDB, mock.Mock)

    def test_create_with_dict(self):
        test_id = 'test trade id'

        self.db.create(utils.test_trade_dict, test_id)

        self.db.db.put.assert_called_with(
            str.encode(test_id),
            str.encode(str(utils.test_trade)))

    def test_create_with_trade(self):
        test_id = 'test trade id'

        self.db.create(utils.test_trade, test_id)

        self.db.db.put.assert_called_with(
            str.encode(test_id),
            str.encode(json.dumps(utils.test_trade_dict,
                                  sort_keys=True,
                                  indent=4)))

    def test_create_with_error(self):
        with self.assertRaises(ValueError) as context:
            self.db.create('this is not valid input', 'trade_id')

        self.assertTrue(
            'Expected dictionary or Trade object'
            in str(context.exception))

    def test_createByFundtx_with_dict(self):
        self.db.createByFundtx(utils.test_trade_dict)

        self.db.db.put.assert_called_with(
            str.encode('5c5e91a89a08b2d6698f50c9fd9bb2fa22da6c74e226c3dd63d'
                       '59511566a2fdb'),
            str.encode(str(utils.test_trade)))

    def test_createByFundtx_with_trade(self):
        self.db.createByFundtx(utils.test_trade)

        self.db.db.put.assert_called_with(
            str.encode('5c5e91a89a08b2d6698f50c9fd9bb2fa22da6c74e226c3dd63d'
                       '59511566a2fdb'),
            str.encode(json.dumps(utils.test_trade_dict,
                                  sort_keys=True,
                                  indent=4)))

    def test_createByFundtx_with_error(self):
        with self.assertRaises(ValueError) as context:
            self.db.createByFundtx('this is not valid input')

        self.assertTrue(
            'Expected dictionary or Trade object'
            in str(context.exception))

    def test_get(self):
        pass

    def test_save_secret(self):
        pass

    def test_get_secret(self):
        pass

    def test_dump(self):
        pass

    def test_print_entries(self):
        pass
