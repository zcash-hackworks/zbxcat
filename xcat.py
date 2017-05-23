import zXcat
import bXcat
from utils import *
from waiting import *
from time import sleep
import json
import os
from pprint import pprint

def check_p2sh(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in btc p2sh")
        return bXcat.check_funds(address)
    else:
        print("Checking funds in zec p2sh")
        return zXcat.check_funds(address)

def set_price():
    trade = {}
    #TODO: make currencies interchangeable. Save to a tuple?
    sell = input("Which currency would you like to trade out of? (bitcoin)")
    sell = 'bitcoin'
    buy = 'zcash'
    sell_amt = input("How much {0} do you want to sell?".format(sell))
    buy_amt = input("How much {0} do you want to receive in exchange?".format(buy))
    sell = {'currency': sell, 'amount': 1.2}
    buy = {'currency': buy, 'amount': 2.45}
    trade['sell'] = sell
    trade['buy'] = buy
    save_trade(trade)

def create_htlc(currency, funder, redeemer, secret, locktime):
    if currency == 'bitcoin':
        sell_p2sh = bXcat.hashtimelockcontract(funder, redeemer, secret, locktime)
    else:
        sell_p2sh = zXcat.hashtimelockcontract(funder, redeemer, secret, locktime)
    return sell_p2sh

def fund_htlc(currency, p2sh, amount):
    if currency == 'bitcoin':
        txid = bXcat.fund_htlc(p2sh, amount)
    else:
        txid = zXcat.fund_htlc(p2sh, amount)
    return txid

def initiate_trade():
    trade = get_trade()
    currency = trade['sell']['currency']
    secret = input("Initiating trade: Enter a password to place the {0} you want to sell in escrow: ".format(currency))
    # TODO: hash and store secret only locally.
    secret = 'test'
    locktime = 20 # Must be more than first tx

    # Returns contract obj
    contracts = {}
    contract = create_htlc(currency, trade['sell']['initiator'], trade['sell']['fulfiller'], secret, locktime)
    sell_p2sh = contract['p2sh']
    contracts[sell_p2sh] = contract
    
    print('To complete your sell, send {0} {1} to this p2sh: {2}'.format(trade['sell']['amount'], currency, contract['p2sh']))
    response = input("Type 'enter' to allow this program to send funds on your behalf.")
    print("Sent")

    sell_amt = trade['sell']['amount']
    txid = fund_htlc(currency, sell_p2sh, sell_amt)

    trade['sell']['p2sh'] = sell_p2sh
    trade['sell']['fund_tx'] = txid
    trade['sell']['status'] = 'funded'
    # TODO: Save secret locally for seller
    trade['sell']['secret'] = secret
    save_trade(trade)

    buy_currency = trade['buy']['currency']
    buy_initiator = trade['buy']['initiator']
    buy_fulfiller = trade['buy']['fulfiller']
    print("Now creating buy contract on the {0} blockchain where you will wait for fulfiller to send funds...".format(buy_currency))
    buy_p2sh = create_htlc(buy_currency, buy_fulfiller, buy_initiator, secret, locktime)
    contracts[buy_p2sh['p2sh']] = buy_p2sh
    contracts[buy_p2sh['p2sh']]['secret']=secret # Ariel: Added, think this should be here
    
    save_contract(contracts)

    print("Waiting for buyer to send funds to this p2sh", buy_p2sh)

    trade['buy']['p2sh'] = buy_p2sh

    save_trade(trade)

def get_addresses():
    trade = get_trade()
    sell = trade['sell']['currency']
    buy = trade['buy']['currency']

    init_offer_addr = input("Enter your {0} address: ".format(sell))
    init_offer_addr = 'mpxpkAUatZR45rdrWQSjkUK7z9LyeSMoEr'
    init_bid_addr = input("Enter your {0} address: ".format(buy))
    init_bid_addr = 'tmTyZswGado9yHsovF3G2z65vzcoy66jX22'   # 'tmWnA7ypaCtpG7KhEWfr5XA1Rpm8521yMfX'
    trade['sell']['initiator'] = init_offer_addr
    trade['buy']['initiator'] = init_bid_addr

    fulfill_offer_addr = input("Enter the {0} address of the party you want to trade with: ".format(sell))
    fulfill_offer_addr = 'mg1EHcpWyErmGhMvpZ9ch2qzFE7ZTKuaEy'
    fulfill_bid_addr = input("Enter the {0} address of the party you want to trade with: ".format(buy))
    fulfill_bid_addr =  'tmTyZswGado9yHsovF3G2z65vzcoy66jX22' # 'tmTqTsBFkeKXyawHfZfcAZQY47xEhpEbo1E'
    trade['sell']['fulfiller'] = fulfill_offer_addr
    trade['buy']['fulfiller'] = fulfill_bid_addr

    # zec_funder, zec_redeemer = zXcat.get_keys(zec_fund_addr, zec_redeem_addr)
    trade['id'] = 1

    save_trade(trade)

def buyer_fulfill():
    trade = get_trade()

    print('trade', trade)
    buy_p2sh = trade['buy']['p2sh']
    sell_p2sh = trade['sell']['p2sh']

    buy_amount = check_p2sh(trade['buy']['currency'], buy_p2sh)
    sell_amount = check_p2sh(trade['sell']['currency'], sell_p2sh)

    input("The seller's p2sh is funded with {0} {1}, type 'enter' if this is the amount you want to buy in {1}.".format(trade['sell']['amount'], trade['sell']['currency']))

    amount = trade['buy']['amount']
    currency = trade['buy']['currency']
    if buy_amount == 0:
        input("You have not send funds to the contract to buy {1} (amount: {0}), type 'enter' to fund.".format(amount, currency))
        p2sh = trade['buy']['p2sh']
        input("Type 'enter' to allow this program to send the agreed upon funds on your behalf")
        txid = fund_htlc(currency, p2sh, amount)
        trade['buy']['fund_tx'] = txid
    else:
        print("It looks like you've already funded the contract to buy {1}, the amount in escrow in the p2sh is {0}.".format(amount, currency))
        print("Please wait for the seller to remove your funds from escrow to complete the trade.")

    save_trade(trade)

def check_blocks(p2sh):
    # blocks = []
    with open('watchdata', 'r') as infile:
        for line in infile:
            res = bXcat.search_p2sh(line.strip('\n'), p2sh)
            # blocks.append(line.strip('\n'))
    # print(blocks)
    # for block in blocks:
    #     res = bXcat.search_p2sh(block, p2sh)

def redeem_p2sh(currency, p2sh, side):
    if currency == 'bitcoin':
        res = bXcat.redeem(p2sh, side)
    else:
        res = zXcat.redeem(p2sh, side)
    return res

def seller_redeem():
    # add locktime as variable?
    trade = get_trade()
    print("trade", trade)
    # Seller redeems buyer's funded tx (contract in p2sh)
    p2sh = trade['buy']['p2sh']['p2sh']   
    currency = trade['buy']['currency']  #Ariel: Changed this to buy, think that's what you meant
    redeem_p2sh(currency, p2sh, 'buy')

def buyer_redeem():
    trade = get_trade()
    # Buyer redeems seller's funded tx
    p2sh = trade['buy']['p2sh']['p2sh']
    currency = trade['sell']['currency']
    print("p2sh:", p2sh)
    zXcat.find_secret(p2sh) # currently assuming the buyer is on the Zcash side, i.e., selling zec for btc
    redeem_p2sh(currency, p2sh, 'sell')

if __name__ == '__main__':
    role = input("Would you like to initiate or accept a trade?")
    # Have initiator propose amounts to trade

    # TODO: Get trade indicated by id number
    # TODO: pass trade into functions?
    # TODO: workflow framed as currency you're trading out of being sell. appropriate?
    trade = get_trade()

    if role == "i":
        if 'status' not in trade['sell']:
            set_price()
            get_addresses()
            initiate_trade()
            print("XCATDB Trade", trade)
        elif 'status' in trade['sell']:
            if trade['sell']['status'] == 'funded':
                # Means buyer has already funded the currency the transaction initiator wants to exchange into
                # Ariel: No - it just means sellet has funded.
                seller_redeem()
    else:
        # if 'status' not in trade['buy']:
        if trade['sell']['status'] == 'funded':
            trade = get_trade()
            buyer_fulfill()
            # How to monitor if txs are included in blocks -- should use blocknotify and a monitor daemon?
            # For regtest, can mock in a function
            # p2sh = trade['buy']['p2sh']
            # check_blocks(p2sh)
        elif trade['sell']['status'] == 'redeemed':
            # Seller has redeemed buyer's tx, buyer can now redeem.
            buyer_redeem()

        pprint(get_trade())
