import zXcat
import bXcat
from xcat import *

print("Starting test of xcat...")

def Zcash_getaddr():
    return zXcat.zcashd.getnewaddress()


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
def Zcash_get_secret(p2sh,fund_txid):
    return zXcat.find_secret(p2sh,fund_tx)

def Zcash_refund(contract):
    return zXcat.redeem_after_timelock(contract)

# returns txid of redeem transaction with secret
def Zcash_redeem(contract,secret):
    txid = zXcat.redeem_with_secret(contract,secret)
    return txid
