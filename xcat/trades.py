import json

class Trade(object):
    def __init__(self, sell=None, buy=None, commitment=None):
        '''Create a new trade with a sell contract and buy contract across two chains'''
        self.sell = sell
        self.buy = buy
        self.commitment = commitment

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

class Contract(object):
    def __init__(self, data):
        # Keep track of funding and redeem tx?
        allowed = ('fulfiller', 'initiator', 'currency', 'p2sh', 'amount', 'fund_tx', 'redeem_tx', 'secret', 'redeemScript', 'redeemblocknum', 'locktime')
        for key in data:
            if key in allowed:
                setattr(self, key, data[key])

    def get_status(self):
        # keep as function or set as property?
        if hasattr(self, 'redeem_tx'):
            return 'redeemed'
        elif hasattr(self, 'refund_tx'):
            return 'refunded'
        elif hasattr(self, 'fund_tx'):
            # Do additional validation here to check amts on blockchain
            return 'funded'
        else:
            return 'empty'
