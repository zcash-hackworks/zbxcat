import hashlib
import json
import random
import binascii
import trades

def hex2str(hexstring):
    return binascii.unhexlify(hexstring).decode('utf-8')

def sha256(secret):
    preimage = secret.encode('utf8')
    h = hashlib.sha256(preimage).digest()
    return h

def generate_password():
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    passlen = 8
    p =  "".join(random.sample(s,passlen))
    return p

# TODO: Port these over to leveldb or some other database
def save_trade(trade):
    with open('xcat.json', 'w') as outfile:
        json.dump(trade, outfile)

def save_seller_trade(trade):
    with open('sellertrade.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def save_buyer_trade(trade):
    with open('buyertrade.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def save_init(trade):
    with open('init.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def get_init():
    with open('init.json') as data_file:
        xcatdb = json.load(data_file)
        sellContract = trades.Contract(xcatdb['sell'])
        buyContract = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sellContract,buyContract)
        return trade


def get_trade():
    with open('xcat.json') as data_file:
    # try:
        xcatdb = json.load(data_file)
        sellContract = trades.Contract(xcatdb['sell'])
        buyContract = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sellContract,buyContract)
        
        return trade

def get_seller_trade():
    with open('init.json') as data_file:
    # try:
        xcatdb = json.load(data_file)
        sellContract = trades.Contract(xcatdb['sell'])
        buyContract = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sellContract,buyContract)
        
        return trade

def get_buyer_trade():
    with open('buyertrade.json') as data_file:
    # try:
        xcatdb = json.load(data_file)
        sellContract = trades.Contract(xcatdb['sell'])
        buyContract = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sellContract,buyContract)
        
        return trade


def erase_trade():
    with open('xcat.json', 'w') as outfile:
        outfile.write('')

# caching the secret locally for now...
def get_secret():
    with open('secret.json') as data_file:
        for line in data_file:
                return line.strip('\n')

def save_secret(secret):
    with open('secret.json', 'w') as outfile:
        outfile.write(secret)

def save(trade):
    print("Saving trade")
    trade = {
    'sell': trade.sellContract.__dict__,
    'buy': trade.buyContract.__dict__
    }
    save_trade(trade)

def jsonformat(trade):
    return {
    'sell': trade.sellContract.__dict__,
    'buy': trade.buyContract.__dict__
    }

