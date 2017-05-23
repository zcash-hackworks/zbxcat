

class Contract(object):
    def __init__(self, funder=None, redeemer=None, blockchain=None):
        '''Create a new hash time-locked contract'''
        self.funder = funder
        self.redeemer = redeemer
        self.blockchain = blockchain
