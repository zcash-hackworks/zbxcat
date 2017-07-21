class Trade(object):
    def __init__(self, sellContract=None, buyContract=None):
        '''Create a new trade with a sell contract and buy contract across two chains'''
        self.sellContract = sellContract
        self.buyContract = buyContract

class Contract(object):
    def __init__(self, data):
        # Keep track of funding and redeem tx?
        allowed = ('funder', 'redeemer', 'currency', 'p2sh', 'amount', 'fund_tx', 'redeem_tx', 'secret', 'redeemscript', 'redeemblocknum','hash_of_secret')
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

# other classes; transactions? users?
