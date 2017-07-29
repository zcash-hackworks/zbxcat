import unittest, json
import xcat.db as db
import xcat.trades as trades
from xcat.tests.utils import test_trade

class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.data = test_trade
        self.sell = trades.Contract(self.data['sell'])

    def test_create(self):
        db.create(self.data, 'test')

    def test_get(self):
        trade = db.get('test')
        tradejson = json.loads(trade.toJSON())
        datajson = json.loads(json.dumps(self.data))
        self.assertEqual(datajson['sell'], tradejson['sell'])
        self.assertEqual(datajson['buy'], tradejson['buy'])
        self.assertEqual(datajson['commitment'], tradejson['commitment'])

if __name__ == '__main__':
    unittest.main()
