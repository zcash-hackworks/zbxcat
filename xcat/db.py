import plyvel
import json
import xcat.utils as utils
from xcat.trades import Trade, Contract


class DB():

    def __init__(self):
        self.db = plyvel.DB('/tmp/xcatDB', create_if_missing=True)
        self.preimageDB = plyvel.DB('/tmp/preimageDB', create_if_missing=True)

    #############################################
    ######## Trades stored by tradeid ###########
    #############################################

    # Takes dict or obj, saves json str as bytes
    def create(self, trade, tradeid):
        if type(trade) == dict:
            trade = json.dumps(trade)
        else:
            trade = trade.toJSON()
        self.db.put(utils.b(tradeid), utils.b(trade))

    #  Uses the funding txid as the key to save trade
    def createByFundtx(self, trade):
        trade = trade.toJSON()
        # # Save trade by initiating txid
        jt = json.loads(trade)
        txid = jt['sell']['fund_tx']
        self.db.put(utils.b(txid), utils.b(trade))

    def get(self, tradeid):
        rawtrade = self.db.get(utils.b(tradeid))
        tradestr = str(rawtrade, 'utf-8')
        trade = self.instantiate(tradestr)
        return trade

    def instantiate(self, trade):
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
    def save_secret(self, tradeid, secret):
        self.preimageDB.put(utils.b(tradeid), utils.b(secret))

    def get_secret(self, tradeid):
        secret = self.preimageDB.get(utils.b(tradeid))
        secret = str(secret, 'utf-8')
        return secret

    #############################################
    ########## Dump or view db entries ##########
    #############################################

    def dump(self):
        results = []
        with self.db.iterator() as it:
            for k, v in it:
                j = json.loads(utils.x2s(utils.b2x(v)))
                results.append((str(k, 'utf-8'), j))
        return results

    def print_entries(self):
        it = self.db.iterator()
        with self.db.iterator() as it:
            for k, v in it:
                j = json.loads(utils.x2s(utils.b2x(v)))
                print("Key:", k)
                print('val: ', j)
                # print('sell: ', j['sell'])
