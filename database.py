import plyvel
from utils import *
import binascii
import sys
import json

db = plyvel.DB('/tmp/testdb', create_if_missing=True)

trade = get_trade()
## txid we retrieve by
if trade and trade.sell:
    if hasattr(trade.sell, 'fund_tx'):
        txid = trade.sell.fund_tx

# Takes object, saves json as bytes
def create(trade):
    trade = trade.toJSON()
    jt = json.loads(trade)
    txid = jt['sell']['fund_tx']
    # Save trade by initiating txid
    db.put(b(txid), b(trade))

def get(txid):
    return db.get(b(txid))

# db.delete(b'hello')

# hexstr = get(txid)
# print(x2s(hexstr))
#
def print_entries():
    it = db.iterator()
    with db.iterator() as it:
        for k, v in it:
            j = json.loads(x2s(b2x(v)))
            print('val: ', j)
            print('sell: ', j['sell'])

# print_entries()
# txid = '1171aeda64eff388b3568fa4675d0ca78852911109bbe42e0ef11ad6bf1b159e'
# entry = db.get(b(txid))
# print(entry)
# print(it.next())
