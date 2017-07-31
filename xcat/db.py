import plyvel
from xcat.utils import *
import binascii
import sys
import json
import ast
from xcat.trades import *

db = plyvel.DB('/tmp/testdb', create_if_missing=True)

# Takes dict or obj, saves json str as bytes
def create(trade, tradeid):
    if type(trade) == dict:
        trade = json.dumps(trade)
    else:
        trade = trade.toJSON()
    db.put(b(tradeid), b(trade))

#  Uses the funding txid as the key to save trade
def createByFundtx(trade):
    trade = trade.toJSON()
    # # Save trade by initiating txid
    jt = json.loads(trade)
    txid = jt['sell']['fund_tx']
    db.put(b(txid), b(trade))

def get(txid):
    rawtrade = db.get(b(txid))
    tradestr = str(rawtrade, 'utf-8')
    trade = instantiate(tradestr)
    return trade

def instantiate(trade):
    if type(trade) == str:
        tradestr = json.loads(trade)
        trade = Trade(buy=Contract(tradestr['buy']), sell=Contract(tradestr['sell']), commitment=tradestr['commitment'])
        return trade



# db.delete(b'hello')
# testtrade = get('test')
# testtrade = instantiate(testtrade)
# print(testtrade)

# hexstr = get(txid)
# print(x2s(hexstr))

def print_entries():
    it = db.iterator()
    with db.iterator() as it:
        for k, v in it:
            j = json.loads(x2s(b2x(v)))
            print("Key:", k)
            print('val: ', j)
            # print('sell: ', j['sell'])

# print_entries()
# txid = '1171aeda64eff388b3568fa4675d0ca78852911109bbe42e0ef11ad6bf1b159e'
# entry = db.get(b(txid))
# print(entry)
# print(it.next())
