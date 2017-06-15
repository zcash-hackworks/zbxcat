import hashlib
import json
import random
import binascii

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

def get_trade():
    with open('xcat.json') as data_file:
        try:
            xcatdb = json.load(data_file)
            return xcatdb
        except:
            return None

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
