import hashlib, json, random, binascii
import trades

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
    if parse_addrs(contract.initiator):
        return 'initiator'
    else:
        return 'fulfiller'

def parse_addrs(address):
    if address[:1] == 'm':
        status = bXcat.validateaddress(address)
    else:
        status = zXcat.validateaddress(address)
    status = status['ismine']
    print("Address {0} is mine: {1}".format(address, status))
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
    with open('secret.json') as data_file:
        for line in data_file:
                return line.strip('\n')

def save_secret(secret):
    with open('secret.json', 'w+') as outfile:
            outfile.write(secret)

#############################################
#########  xcat.json temp file  #############
#############################################

def save_trade(trade):
    print("Trade in save_trade", trade)
    with open('xcat.json', 'w+') as outfile:
        json.dump(trade, outfile)

def get_trade():
    try:
        with open('xcat.json') as data_file:
            xcatdb = json.load(data_file)
            sell = trades.Contract(xcatdb['sell'])
            buy = trades.Contract(xcatdb['buy'])
            trade = trades.Trade(sell, buy)
            return trade
    except:
        return None

def erase_trade():
    with open('xcat.json', 'w') as outfile:
        outfile.write('')

def save(trade):
    print("Saving trade")
    trade = {
    'sell': trade.sell.__dict__,
    'buy': trade.buy.__dict__
    }
    save_trade(trade)


#############################################
######### Ariel's changes     ###############
#############################################


def save_seller_trade(trade):
    with open('sellertrade.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def save_buyer_trade(trade):
    with open('buyertrade.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def save_init(trade):
    with open('init.json', 'w') as outfile:
        json.dump(jsonformat(trade), outfile)

def get_seller_trade():
    data_file = open('init.json', 'w+')
    # try:
    xcatdb = json.load(data_file)
    sell = trades.Contract(xcatdb['sell'])
    buyContract = trades.Contract(xcatdb['buy'])
    trade = trades.Trade(sell,buyContract)

    return trade

def get_buyer_trade():
    with open('buyertrade.json') as data_file:
    # try:
        xcatdb = json.load(data_file)
        sell = trades.Contract(xcatdb['sell'])
        buyContract = trades.Contract(xcatdb['buy'])
        trade = trades.Trade(sell,buyContract)

        return trade
