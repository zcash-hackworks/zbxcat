
class Contract(object):
    def __init__(self, data):
        # Keep track of funding and redeem tx?
        allowed = ('fulfiller', 'initiator', 'currency', 'p2sh', 'amount', 'fund_tx', 'redeem_tx', 'secret', 'redeemScript', 'redeemblocknum')
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

    # def __init__(self, **kwargs):
    #     # initiator=None, fulfiller=None, currency=None, p2sh=None, amount=None, preimage=None
    #     print('kwargs in init', kwargs)
    #     # print(type(*data))
    #     '''Create a new hash time-locked contract'''
    #     self.initiator = kwargs['initiator']
    #     self.fulfiller = kwargs['fulfiller']
    #     self.currency = kwargs['currency']
    #     self.p2sh = kwargs['p2sh']
    #     self.amount = kwargs['amount']
    #     if 'preimage' in kwargs:
    #         self.preimage = kwargs['preimage']
    #     # have a 'status' property, for empty, funded, refunded, or redeemed

    # def __str__(self):
    #     return self

    # how to distinguish buy and sell contracts? use syntax new Contract()? Remember self's pupbkey?
    # def createBuy():

# Intitialize a trade and then create the contracts?
class Trade(object):
    def __init__(self, sellContract=None, buyContract=None):
        '''Create a new trade with a sell contract and buy contract across two chains'''
        self.sellContract = sellContract
        self.buyContract = buyContract



# other classes; transactions? users?

class Participant(object):
    def __init__(self, zcashAddr=None, bitcoinAddr=None):
        self.zcashAddr=None
        self.bitcoinAddr=None
