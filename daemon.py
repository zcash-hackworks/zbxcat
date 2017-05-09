from ZBXCAT.BitcoinRPC.BDaemon import *

bd = BDaemon('REGTEST')
# v = bd.getVersion()
# print(v)

def generate(num):
    gen = bd.generate(num)
    print("Generated blocks", gen)

def fund_p2sh(p2sh, amount):
    fund_tx = bd.sendtoaddress(p2sh, amount)
    return fund_tx

def tx_details(txid):
    tx = bd.gettransaction(txid)
    details = tx['details'][0]
    return details

# These two methods are placeholders
def get_recipient_address():
    address = bd.getnewaddress()
    return address

def get_sender_address():
    address = bd.getnewaddress()
    return address

def importaddress(addr):
    res = bd.importaddress(addr)
    return res

def sendrawtx(hex):
    txid = bd.sendrawtransaction(hex)
    return txid
