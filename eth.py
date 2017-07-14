import zXcat
import bXcat
from xcat import *
from zXcat import b2x,lx
print("Starting test of xcat...")

def Zcash_getaddr():
    return zXcat.zcashd.getnewaddress()

def Zcash_generate(i):
    zXcat.zcashd.generate(i)

def Zcash_fund(contract,amount):
    p2sh = contract['p2sh']
    fund_txid = zXcat.zcashd.sendtoaddress(p2sh,amount)
    contract['fund_tx'] = fund_txid
    return contract

def Zcash_make_contract(funder, redeemer, hash_of_secret, lock_increment):
    contract = zXcat.make_hashtimelockcontract(funder, redeemer, hash_of_secret, lock_increment)
    return contract

'''def Zcash_make_contract_random(funder, redeemer, hash_of_secret, lock_increment):
    contract = zXcat.make_hashtimelockcontract(funder, redeemer, hash_of_secret, lock_increment)
    return contract
'''

# finds seller's redeem tx and gets secret from it
def Zcash_get_secret(contract):
    print("HERE", b2x(lx(b2x(contract['fund_tx']))))
    return zXcat.find_secret(contract['p2sh'], b2x(lx(b2x(contract['fund_tx']))))

def Zcash_refund(contract):
    contractobj = Contract(contract)
    return zXcat.redeem_after_timelock(contract)

# returns txid of redeem transaction with secret
def Zcash_redeem(contract, secret):
    contractobj = Contract(contract)
    txid = zXcat.redeem_with_secret(contractobj, secret)
    return txid

