import zXcat
import bXcat
from utils import *
from waiting import *
from time import sleep
import json
import os, sys
from pprint import pprint
from trades import Contract, Trade
import userInput

#compute redeemblocknum according to current block
def compute_redeemblocknum(currency, increment):
    if currency == 'bitcoin':
        redeemblocknum = bXcat.bitcoind.getblockcount()+int(increment)
    else:
        redeemblocknum = zXcat.zcashd.getblockcount()+int(increment)
    return redeemblocknum

#import p2sh address according to contract details
def import_p2sh(currency, p2sh):
    return
   # if currency == 'bitcoin':
       # bXcat.import_address(p2sh)
   # else:
       # zXcat.import_address(p2sh)


def check_p2sh(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in Bitcoin p2sh")
        return bXcat.check_funds(address)
    else:
        print("Checking funds in Zcash p2sh")
        return zXcat.check_funds(address)

def create_htlc(contract):
    if contract.currency == 'bitcoin':
        contract = bXcat.hashtimelockcontract(contract)
    else:
        contract = zXcat.hashtimelockcontract(contract)
    return contract

def fund_htlc(currency, p2sh, amount):
    if currency == 'bitcoin':
        txid = bXcat.fund_htlc(p2sh, amount)
    else:
        txid = zXcat.fund_htlc(p2sh, amount)
    return txid

def fund_buy_contract(trade):
    buy = trade.buyContract
    txid = fund_htlc(buy.currency, buy.p2sh, buy.amount)
    setattr(trade.buyContract, 'fund_tx', txid)
    save(trade)
    return txid

def fund_sell_contract(trade):
    sell = trade.sellContract
    txid = fund_htlc(sell.currency, sell.p2sh, sell.amount)
    setattr(trade.sellContract, 'fund_tx', txid)
    save(trade)
    return txid


# updates the contract with the p2sh address and redeemscript generated according to the data in the contract
def create_and_import_p2sh(contract):
    contract = create_htlc(contract)
    import_p2sh(contract.currency,contract.p2sh)
    print("sell contract", contract)
    setattr(contract, 'p2sh', contract.p2sh)
    setattr(contract, 'redeemscript', contract.redeemscript)
    setattr(contract, 'redeemblocknum', contract.redeemblocknum)
    return contract



def create_sell_p2sh(trade, secret, locktime):
    # CREATE SELL CONTRACT
    sell = trade.sellContract
    contract = create_htlc(sell.currency, sell.initiator, sell.fulfiller, hash_of_secret, locktime)
    print("sell contract", contract)
    setattr(trade.sellContract, 'p2sh', contract['p2sh'])
    setattr(trade.sellContract, 'redeemScript', contract['redeemScript'])
    setattr(trade.sellContract, 'redeemblocknum', contract['redeemblocknum'])
    save(trade)

def create_buy_2sh(trade, secret, locktime):
    ## CREATE BUY CONTRACT
    buy = trade.buyContract
    print("Now creating buy contract on the {0} blockchain where you will wait for the buyer to send funds...".format(buy.currency))
    print("HTLC DETAILS", buy.currency, buy.fulfiller, buy.initiator, hash_of_secret, locktime)
    buy_contract = create_htlc(buy.currency, buy.fulfiller, buy.initiator, hash_of_secret, locktime)
    print("Buy contract", buy_contract)

    setattr(trade.buyContract, 'p2sh', buy_contract['p2sh'])
    setattr(trade.buyContract, 'redeemScript', buy_contract['redeemScript'])
    setattr(trade.buyContract, 'redeemblocknum', buy_contract['redeemblocknum'])
    print("Now contact the buyer and tell them to send funds to this p2sh: ", trade.buyContract.p2sh)
    import_p2sh(buy)
    save(trade)

# we try to redeem contract with secret
# we try to redeem revertcontract with time lock
# returns True if at least one redeem succeeded
def redeem_p2sh(contract, secret, revertcontract):

    currency = contract.currency
    res = False 
    revert_currency = revertcontract.currency

    if (currency == 'bitcoin' and bXcat.still_locked(contract)):
        print("trying to redeem btc with secret:")
        try:
            res = bXcat.redeem_with_secret(contract, secret)
        except Exception:
            print("Failed - you might not have the correct secret - perhaps because the seller has not redeemed the buy contract correctly")
        if(res): print("You have redeemed {0} {1}!".format(contract.amount, contract.currency))
    
    if (currency == 'zcash' and zXcat.still_locked(contract)):
        print("trying to redeeming zec with secret:")
        try:
            res = zXcat.redeem_with_secret(contract, secret)
        except Exception:
            print("Failed - you might not have the correct secret - perhaps because the seller has not redeemed the buy contract correctly")
        if(res): print("You have redeemed {0} {1}!".format(contract.amount, contract.currency))
    if (revert_currency == 'bitcoin'):
        if(bXcat.still_locked(revertcontract)):
            print('too early for redeeminng with time lock on btc chain')
        else:        
            print("trying to redeeming btc with timelock:")
            try:
                res = bXcat.redeem_after_timelock(revertcontract)
            except Exception:
                print("Failed - the other party might have redeemed the fund tx on the btc chain with the secret by now") 
            if(res): print("You have redeemed {0} {1}!".format(revertcontract.amount, revertcontract.currency))   
    if (revert_currency == 'zcash'):
        if(zXcat.still_locked(revertcontract)):
            print('too early for redeeminng with time lock on zcash chain')
        else:        
            print("trying to redeeming zec with timelock:")
            try:
                res = zXcat.redeem_after_timelock(revertcontract)
            except Exception:
                print("Failed - the other party might have redeemed the fund tx on the zcash chain with the secret by now") 
            if(res): print("You have redeemed {0} {1}!".format(revertcontract.amount, revertcontract.currency))   

    return res

def print_trade(role):
    print("\nTrade status for {0}:".format(role))
    trade = get_trade()
    pprint(trade)

# ####  Main functions determining user flow from command line
# def buyer_redeem(trade):
#     userInput.authorize_buyer_redeem(trade)
#     if trade.sellContract.get_status() == 'redeemed':
#         print("You already redeemed the funds and acquired {0} {1}".format(trade.sellContract.amount, trade.sellContract.currency))
#         exit()
#     else:
#         # Buyer redeems seller's funded tx
#         p2sh = trade.sellContract.p2sh
#         currency = trade.sellContract.currency
#         # Buy contract is where seller disclosed secret in redeeming
#         if trade.buyContract.currency == 'bitcoin':
#             secret = bXcat.parse_secret(trade.buyContract.redeem_tx)
#         else:
#             secret = zXcat.parse_secret(trade.buyContract.redeem_tx)
#         print("Found secret in seller's redeem tx", secret)
#         redeem_tx = redeem_p2sh(trade.sellContract, secret)
#         setattr(trade.sellContract, 'redeem_tx', redeem_tx)
#         save(trade)
#     exit()

# def seller_redeem(trade):
#     buy = trade.buyContract
#     userInput.authorize_seller_redeem(buy)

#     if trade.sellContract.get_status() == 'redeemed':
#         print("You already redeemed the funds and acquired {0} {1}".format(buy.amount, buy.currency))
#         exit()
#     else:
#         # Seller redeems buyer's funded tx (contract in p2sh)
#         secret = userInput.retrieve_password()
#         tx_type, txid = redeem_p2sh(trade.buyContract, secret)
#         setattr(trade.buyContract, tx_type, txid)
#         save(trade)
#         print("You have redeemed {0} {1}!".format(buy.amount, buy.currency))
#         print_trade('seller')

# def buyer_fulfill(trade):
#     buy = trade.buyContract
#     sell = trade.sellContract
#     buy_p2sh_balance = check_p2sh(buy.currency, buy.p2sh)
#     sell_p2sh_balance = check_p2sh(sell.currency, sell.p2sh)

#     if buy_p2sh_balance == 0:
#         userInput.authorize_buyer_fulfill(sell_p2sh_balance, sell.currency, buy_p2sh_balance, buy.currency)
#         print("Buy amt:", buy.amount)
#         txid = fund_buy_contract(trade)
#         print("Fund tx txid:", txid)
#     else:
#         print("It looks like you've already funded the contract to buy {1}, the amount in escrow in the p2sh is {0}.".format(buy_p2sh_balance, buy.currency))
#         print("Please wait for the seller to remove your funds from escrow to complete the trade.")
#     print_trade('buyer')

def seller_initiate(trade):
    # Get amounts
    amounts = userInput.get_trade_amounts()
    sell = amounts['sell']
    buy = amounts['buy']
    sell_currency = sell['currency']
    buy_currency = buy['currency']
    # Get addresses
    init_addrs = userInput.get_initiator_addresses()
    sell['initiator'] = init_addrs[sell_currency]
    buy['initiator'] = init_addrs[buy_currency]
    fulfill_addrs = userInput.get_fulfiller_addresses()
    sell['fulfiller'] = fulfill_addrs[sell_currency]
    buy['fulfiller'] = fulfill_addrs[buy_currency]
    # initializing contract classes with addresses, currencies, and amounts
    trade.sellContract = Contract(sell)
    trade.buyContract = Contract(buy)
    print(trade.sellContract.__dict__)
    print(trade.buyContract.__dict__)

    secret = userInput.create_password()
    # TODO: Implement locktimes and mock block passage of time
    sell_locktime = 5
    buy_locktime = 10 # Must be more than first tx

    create_sell_p2sh(trade, secret, sell_locktime)

    userInput.authorize_fund_sell(trade)

    txid = fund_sell_contract(trade)
    print("Sent")

    create_buy_p2sh(trade, secret, buy_locktime)
    print_trade('seller')

if __name__ == '__main__':
    print("ZEC <-> BTC XCAT (Cross-Chain Atomic Transactions)")
    print("=" * 50)

    trade = get_trade()

    if trade == None:
        htlcTrade = Trade()
        print("New empty trade")
    else:
        buyContract = Contract(trade['buy'])
        sellContract = Contract(trade['sell'])
        htlcTrade = Trade(buyContract=buyContract, sellContract=sellContract)

    try:
        if sys.argv[1] == 'new':
            erase_trade()
            role = 'seller'
            htlcTrade = Trade()
            print("Creating new XCAT transaction...")
        else:
            role = sys.argv[1]
            print("Your role in demo:", role)
    except:
        if trade == None:
            print("No active trades available.")
            res = input("Would you like to initiate a trade? (y/n) ")
            if res == 'y':
                role = 'seller'
            else:
                exit()
        else:
            print("Trade exists, run script as buyer or seller to complete trade.")
            exit()

    if htlcTrade.buyContract is not None and htlcTrade.sellContract is not None:
        if htlcTrade.sellContract.get_status() == 'redeemed' and htlcTrade.buyContract.get_status() == 'redeemed':
            print("This trade is already complete! Trade details:")
            pprint(trade)
            exit()

    if role == "seller":
        if htlcTrade.sellContract == None:
            seller_initiate(htlcTrade)
        elif htlcTrade.buyContract.get_status() == 'funded':
            seller_redeem(htlcTrade)
        elif htlcTrade.buyContract.get_status() == 'empty':
            print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(htlcTrade.buyContract.currency))
    else:
        # Need better way of preventing buyer from having secret
        # if 'status' not in trade['buy'] and trade['sell']['status'] == 'funded':
        if htlcTrade.sellContract.get_status() == 'funded' and htlcTrade.buyContract.get_status() != 'redeemed':
            print("One active trade available, fulfilling buyer contract...")
            buyer_fulfill(htlcTrade)
            # How to monitor if txs are included in blocks -- should use blocknotify and a monitor daemon?
            # p2sh = trade['buy']['p2sh']
            # check_blocks(p2sh)
        elif htlcTrade.buyContract.get_status() == 'redeemed':
            # Seller has redeemed buyer's tx, buyer can now redeem.
            buyer_redeem(htlcTrade)
            print("XCAT trade complete!")

        # Note: there is some little endian weirdness in the bXcat and zXcat files, need to handle the endianness of txids better & more consistently
