import plyvel
import json
import xcat.utils as utils
from xcat.trades import Trade, Contract

db = plyvel.DB('/tmp/xcatDB', create_if_missing=True)
preimageDB = plyvel.DB('/tmp/preimageDB', create_if_missing=True)

#############################################
######## Trades stored by tradeid ###########
#############################################


# Takes dict or obj, saves json str as bytes
def create(trade, tradeid):
    if type(trade) == dict:
        trade = json.dumps(trade)
    else:
        trade = trade.toJSON()
    db.put(utils.b(tradeid), utils.b(trade))


#  Uses the funding txid as the key to save trade
def createByFundtx(trade):
    trade = trade.toJSON()
    # # Save trade by initiating txid
    jt = json.loads(trade)
    txid = jt['sell']['fund_tx']
    db.put(utils.b(txid), utils.b(trade))


def get(tradeid):
    rawtrade = db.get(utils.b(tradeid))
    tradestr = str(rawtrade, 'utf-8')
    trade = instantiate(tradestr)
    return trade


def instantiate(trade):
    if type(trade) == str:
        tradestr = json.loads(trade)
        trade = Trade(
            buy=Contract(tradestr['buy']),
            sell=Contract(tradestr['sell']),
            commitment=tradestr['commitment'])
        return trade

#############################################
###### Preimages stored by tradeid ##########
#############################################


# Stores secret locally in key/value store by tradeid
def save_secret(tradeid, secret):
    preimageDB.put(utils.b(tradeid), utils.b(secret))


def get_secret(tradeid):
    secret = preimageDB.get(utils.b(tradeid))
    secret = str(secret, 'utf-8')
    return secret


#############################################
########## Dump or view db entries ##########
#############################################

def dump():
    results = []
    with db.iterator() as it:
        for k, v in it:
            j = json.loads(utils.x2s(utils.b2x(v)))
            results.append((str(k, 'utf-8'), j))
    return results


def print_entries():
    it = db.iterator()
    with db.iterator() as it:
        for k, v in it:
            j = json.loads(utils.x2s(utils.b2x(v)))
            print("Key:", k)
            print('val: ', j)
            # print('sell: ', j['sell'])
