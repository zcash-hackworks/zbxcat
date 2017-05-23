import hashlib
import json

def sha256(secret):
    preimage = secret.encode('utf8')
    h = hashlib.sha256(preimage).digest()
    return h

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

def get_contract():
    with open('contract.json') as data_file:
        contractdb = json.load(data_file)
    return contractdb

def save_contract(contracts):
    with open('contract.json', 'w') as outfile:
        json.dump(contracts, outfile)
