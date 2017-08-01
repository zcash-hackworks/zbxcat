import hashlib, json, random, binascii
import xcat.trades as trades
import xcat.bitcoinRPC as bitcoinRPC
import xcat.zcashRPC as zcashRPC

############################################
########### Data conversion utils ##########
############################################
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
    print(hexstr['fund_tx'])
    print(jsonstr)
    return json.loads(jsonstr)

def jsonformat(trade):
    return {
    'sell': trade.sell.__dict__,
    'buy': trade.buyContract.__dict__
    }

############################################
#### Role detection utils ####
############################################
def find_role(contract):
    # Obviously when regtest created both addrs on same machine, role is both.
    if is_myaddr(contract.initiator) and is_myaddr(contract.fulfiller):
        return 'test'
    elif is_myaddr(contract.initiator):
        return 'initiator'
    else:
        return 'fulfiller'

def is_myaddr(address):
    if address[:1] == 'm':
        status = bitcoinRPC.validateaddress(address)
    else:
        status = zcashRPC.validateaddress(address)
    status = status['ismine']
    # print("Address {0} is mine: {1}".format(address, status))
    return status

############################################
########### Preimage utils #################
############################################

def sha256(secret):
    preimage = secret.encode('utf8')
    h = hashlib.sha256(preimage).digest()
    return h

def generate_password():
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    passlen = 8
    p =  "".join(random.sample(s,passlen))
    return p

# caching the secret locally for now...
def get_secret():
    with open('xcat/secret.json') as data_file:
        for line in data_file:
                return line.strip('\n')

def save_secret(secret):
    with open('xcat/secret.json', 'w+') as outfile:
            outfile.write(secret)

#############################################
#########  xcat.json temp file  #############
#############################################

def save_trade(trade):
    print("Trade in save_trade", trade)
    with open('xcat/xcat.json', 'w+') as outfile:
        json.dump(trade, outfile)

def get_trade():
    with open('xcat/xcat.json') as data_file:
        xcatdb = json.load(data_file)
        sell = trades.Contract(xcatdb['sell'])
        buy = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sell, buy, commitment=xcatdb['commitment'])
        return trade

def erase_trade():
    with open('xcat.json', 'w') as outfile:
        outfile.write('')

def save(trade):
    print("Saving trade")
    trade = {
    'sell': trade.sell.__dict__,
    'buy': trade.buy.__dict__,
    'commitment': trade.commitment
    }
    save_trade(trade)
