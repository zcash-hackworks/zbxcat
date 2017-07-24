import hashlib
import json
import random
import binascii

def b(string):
    """Convert a string to bytes"""
    return str.encode(string)

def x(h):
    """Convert a hex string to bytes"""
    return binascii.unhexlify(h.encode('utf8'))

def b2x(b):
    """Convert bytes to a hex string"""
    return binascii.hexlify(b).decode('utf8')

def x2s(hexstring):
    """Convert hex to a utf-8 string"""
    return binascii.unhexlify(hexstring).decode('utf-8')

def s2x(string):
    """Convert a utf-8 string to hex"""
    return b2x(b(string))

def hex2dict(hexstr):
    jsonstr = x2s(hexstr)
    print(jsonstr)
    return json.loads(jsonstr)

######################


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
    try:
        with open('secret.json', 'w') as outfile:
            outfile.write(secret)
    except IOError:
        with open('secret.json', 'w+') as outfile:
            outfile.write(secret)

def save(trade):
    print("Saving trade")
    trade = {
    'sell': trade.sellContract.__dict__,
    'buy': trade.buyContract.__dict__
    }
    save_trade(trade)
