import zXcat
import bXcat
from xcat import *

print("Starting test of xcat...")

def Zcash_getaddr()
    return zXcatForEth.zcashd.getnewaddresss()


def Zcash_fund(p2sh,amount)
    fund_txid = zXcatForEth.zcashd.sendtoaddress(p2sh,amount)
    return fund_txid

def Zcash_getredeemscript_andp2sh(seller, buyer, hash_of_secret, lock_increment)
    return zXcatForEth.hashtimelockcontract(seller, buyer, hash_of_secret, lock_increment)

# finds seller's redeem tx and gets secret from it
def Zcash_get_secret(p2sh,fund_txid)
    return zXcatForEth.find_secret(p2sh,fund_tx)

def Zcash_refund(redeemscript,buyer_ad,p2sh,fund_txid)
    return zXcatForEth.

def Zcash_redeem(redeemscript,secret,p2sh, amount):

    txid = zXcatForETH.redeem_with_secret(trade.buyContract, secret, trade.sellContract)
    return txid

def redeem_buyer():
    print("BUYER REDEEMING SELL CONTRACT")
    print("=============================")
    trade = get_trade()
    buyContract = trade.buyContract
    sellContract = trade.sellContract
    secret = ""
    # if sellContract.get_status() == 'redeemed':
    #     raise RuntimeError("Sell contract was redeemed before buyer could retrieve funds")
    # elif buyContract.get_status() == 'refunded':
    #     print("buyContract was refunded to buyer")
    # else:
    # Buy contract is where seller disclosed secret in redeeming
    if buyContract.currency == 'bitcoin':
        if (bXcat.still_locked(buyContract)):
            if(not hasattr(buyContract,'fund_tx')):
                print("Seems address has not been funded yet. Aborting.")
                quit()
            secret = bXcat.find_secret(buyContract.p2sh,buyContract.fund_tx)
            if(secret != ""):
                print("Found secret in seller's redeem tx on bitcoin chain:", secret)
    else:
        if zXcat.still_locked(buyContract):
            secret = zXcat.find_secret(buyContract.p2sh,buyContract.fund_tx)
            if(secret != ""):
                print("Found secret in seller's redeem tx on zcash chain:", secret)
    redeem_tx = redeem_p2sh(sellContract, secret, buyContract)
    setattr(trade.sellContract, 'redeem_tx', redeem_tx)
    save(trade)


def generate_blocks(num):
    bXcat.generate(num)
    zXcat.generate(num)

