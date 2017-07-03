import plyvel
from utils import *
import binascii
import sys

db = plyvel.DB('/tmp/testdb', create_if_missing=True)

trade = get_trade()
## txid we retrieve by
txid = trade['sell']['fund_tx']

def hex2dict(hexstr):
    jsonstr = x2s(hexstr)
    return json.loads(jsonstr)

def create(hexstr):
    trade = hex2dict(hexstr)
    txid = trade['sell']['fund_tx']
    # Save trade by initiating txid
    db.put(b(txid), b(hexstr))

def get(txid):
    return db.get(b(txid))

hexstr = get(txid)
print(x2s(hexstr))
