import json


class Trade():
    def __init__(self, sell=None, buy=None, commitment=None,
                 fromJSON=None, fromDict=None):
        '''Create a new trade with buy and sell contracts across two chains'''

        if fromJSON is not None and fromDict is None:
            if isinstance(fromJSON, str):
                fromDict = json.loads(fromJSON)
            else:
                raise ValueError('Expected json string')
        if fromDict is not None:
            self.sell = Contract(fromDict['sell'])
            self.buy = Contract(fromDict['buy'])
            self.commitment = fromDict['commitment']
        else:
            self.sell = sell
            self.buy = buy
            self.commitment = commitment

    def toJSON(self):
        return json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __str__(self):
        return self.toJSON()

    def __repr__(self):
        return 'Trade:\n{0} {1} from {2}\nfor\n{3} {4} from {5}'.format(
            self.sell.amount,
            self.sell.currency,
            self.sell.initiator,
            self.buy.amount,
            self.buy.currency,
            self.buy.initiator)


class Contract():
    def __init__(self, data):
        allowed = ('fulfiller', 'initiator', 'currency', 'p2sh', 'amount',
                   'fund_tx', 'redeem_tx', 'secret', 'redeemScript',
                   'redeemblocknum', 'locktime')
        for key in data:
            if key in allowed:
                setattr(self, key, data[key])

    def get_status(self):
        if hasattr(self, 'redeem_tx'):
            return 'redeemed'
        elif hasattr(self, 'refund_tx'):
            return 'refunded'
        elif hasattr(self, 'fund_tx'):
            # Do additional validation here to check amts on blockchain
            return 'funded'
        else:
            return 'empty'
