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

def check_p2sh(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in Bitcoin p2sh")
        return bXcat.check_funds(address)
    else:
        print("Checking funds in Zcash p2sh")
        return zXcat.check_funds(address)

def create_htlc(currency, funder, redeemer, commitment, locktime):
    if currency == 'bitcoin':
        sell_p2sh = bXcat.hashtimelockcontract(funder, redeemer, commitment, locktime)
    else:
        sell_p2sh = zXcat.hashtimelockcontract(funder, redeemer, commitment, locktime)
    return sell_p2sh

def fund_htlc(currency, p2sh, amount):
    if currency == 'bitcoin':
        txid = bXcat.fund_htlc(p2sh, amount)
    else:
        txid = zXcat.fund_htlc(p2sh, amount)
    return txid
#
# def fund_buy_contract(trade):
#     buy = trade.buy
#     txid = fund_htlc(buy.currency, buy.p2sh, buy.amount)
#     setattr(trade.buy, 'fund_tx', txid)
#     save(trade)
#     return txid

def fund_contract(contract):
    txid = fund_htlc(contract.currency, contract.p2sh, contract.amount)
    return txid

def fund_sell_contract(trade):
    sell = trade.sell
    txid = fund_htlc(sell.currency, sell.p2sh, sell.amount)
    setattr(trade.sell, 'fund_tx', txid)
    save(trade)
    return txid

def create_sell_p2sh(trade, commitment, locktime):
    # CREATE SELL CONTRACT
    sell = trade.sell
    contract = create_htlc(sell.currency, sell.initiator, sell.fulfiller, commitment, locktime)
    print("sell contract", contract)
    setattr(trade.sell, 'p2sh', contract['p2sh'])
    setattr(trade.sell, 'redeemScript', contract['redeemScript'])
    setattr(trade.sell, 'redeemblocknum', contract['redeemblocknum'])
    save(trade)

def create_buy_p2sh(trade, commitment, locktime):
    ## CREATE BUY CONTRACT
    buy = trade.buy
    print("Now creating buy contract on the {0} blockchain where you will wait for the buyer to send funds...".format(buy.currency))
    print("HTLC DETAILS", buy.currency, buy.fulfiller, buy.initiator, commitment, locktime)
    buy_contract = create_htlc(buy.currency, buy.fulfiller, buy.initiator, commitment, locktime)
    print("Buy contract", buy_contract)

    setattr(trade.buy, 'p2sh', buy_contract['p2sh'])
    setattr(trade.buy, 'redeemScript', buy_contract['redeemScript'])
    setattr(trade.buy, 'redeemblocknum', buy_contract['redeemblocknum'])
    print("Now contact the buyer and tell them to send funds to this p2sh: ", trade.buy.p2sh)

    save(trade)

def auto_redeem_p2sh(contract, secret):
    currency = contract.currency
    if currency == 'bitcoin':
        res = bXcat.auto_redeem(contract, secret)
    else:
        res = zXcat.auto_redeem(contract, secret)
    return res


def redeem_p2sh(contract, secret):
    currency = contract.currency
    if currency == 'bitcoin':
        res = bXcat.redeem_contract(contract, secret)
    else:
        res = zXcat.redeem_contract(contract, secret)
    return res

def parse_secret(chain, txid):
    if chain == 'bitcoin':
        secret = bXcat.parse_secret(txid)
    else:
        secret = zXcat.parse_secret(txid)

####  Main functions determining user flow from command line
def buyer_redeem(trade):
    userInput.authorize_buyer_redeem(trade)
    if trade.sell.get_status() == 'redeemed':
        print("You already redeemed the funds and acquired {0} {1}".format(trade.sell.amount, trade.sell.currency))
        exit()
    else:
        # Buyer redeems seller's funded tx
        p2sh = trade.sell.p2sh
        currency = trade.sell.currency
        # Buy contract is where seller disclosed secret in redeeming
        if trade.buy.currency == 'bitcoin':
            secret = bXcat.parse_secret(trade.buy.redeem_tx)
        else:
            secret = zXcat.parse_secret(trade.buy.redeem_tx)
        print("Found secret in seller's redeem tx", secret)
        redeem_tx = redeem_p2sh(trade.sell, secret)
        setattr(trade.sell, 'redeem_tx', redeem_tx)
        save(trade)
    exit()

def seller_redeem_p2sh(trade, secret):
    buy = trade.buy
    userInput.authorize_seller_redeem(buy)

    if trade.sell.get_status() == 'redeemed':
        print("You already redeemed the funds and acquired {0} {1}".format(buy.amount, buy.currency))
        exit()
    else:
        # Seller redeems buyer's funded tx (contract in p2sh)
        tx_type, txid = redeem_p2sh(trade.buy, secret)
        print("Setting tx_type: txid", tx_type, txid)
        setattr(trade.buy, tx_type, txid)
        print("You have redeemed {0} {1}!".format(buy.amount, buy.currency))
    return trade

def buyer_fulfill(trade):
    buy = trade.buy
    sell = trade.sell
    buy_p2sh_balance = check_p2sh(buy.currency, buy.p2sh)
    sell_p2sh_balance = check_p2sh(sell.currency, sell.p2sh)

    if buy_p2sh_balance == 0:
        userInput.authorize_buyer_fulfill(sell_p2sh_balance, sell.currency, buy_p2sh_balance, buy.currency)
        print("Buy amt:", buy.amount)
        txid = fund_buy_contract(trade)
        print("Fund tx txid:", txid)
    else:
        print("It looks like you've already funded the contract to buy {1}, the amount in escrow in the p2sh is {0}.".format(buy_p2sh_balance, buy.currency))
        print("Please wait for the seller to remove your funds from escrow to complete the trade.")
    print_trade('buyer')

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
    trade.sell = Contract(sell)
    trade.buy = Contract(buy)
    print(trade.sell.__dict__)
    print(trade.buy.__dict__)

    secret = userInput.create_password()
    save_secret(secret)
    hash_of_secret = sha256(secret)
    # TODO: Implement locktimes and mock block passage of time
    sell_locktime = 5
    buy_locktime = 10 # Must be more than first tx
    print("Creating pay-to-script-hash for sell contract...")
    create_sell_p2sh(trade, hash_of_secret, sell_locktime)

    userInput.authorize_fund_sell(trade)

    txid = fund_sell_contract(trade)
    print("Sent")

    create_buy_p2sh(trade, secret, buy_locktime)

    trade.commitment = b2x(hash_of_secret)
    return trade
