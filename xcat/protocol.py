import json
import os, sys
from pprint import pprint
from xcat.utils import *
from xcat.trades import Contract, Trade
import xcat.userInput as userInput
import xcat.db as db
from xcat.xcatconf import *
from xcat.bitcoinRPC import bitcoinProxy
from xcat.zcashRPC import zcashProxy
import logging

bitcoinRPC = bitcoinProxy()
zcashRPC = zcashProxy()

def generate(num):
    bitcoinRPC.generate(num)
    zcashRPC.generate(num)

def is_myaddr(address):
    # Handle different network prefixes
    if address[:1] == 'm':
        status = bitcoinRPC.validateaddress(address)
    else:
        status = zcashRPC.validateaddress(address)
    logging.debug("Address status: ", status)
    if status['isvalid'] is False:
        raise ValueError("Invalid address: %s" % address)
    elif 'ismine' in status:
        status = status['ismine']
    return status

def find_secret_from_fundtx(currency, p2sh, fundtx):
    if currency == 'bitcoin':
        secret = bitcoinRPC.find_secret(p2sh, fundtx)
    elif currency == 'zcash':
        secret = zcashRPC.find_secret(p2sh, fundtx)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return secret

def import_addrs(trade):
    check_fund_status(trade.sell.currency, trade.sell.p2sh)
    check_fund_status(trade.buy.currency, trade.buy.p2sh)

def check_p2sh(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in Bitcoin p2sh")
        return bitcoinRPC.check_funds(address)
    elif currency == 'zcash':
        print("Checking funds in Zcash p2sh")
        return zcashRPC.check_funds(address)
    else:
        raise ValueError("Currency not recognized: ", currency)

def check_fund_status(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in Bitcoin p2sh")
        return bitcoinRPC.get_fund_status(address)
    elif currency == 'zcash':
        print("Checking funds in Zcash p2sh")
        return zcashRPC.get_fund_status(address)
    else:
        raise ValueError("Currency not recognized: ", currency)

# TODO: function to calculate appropriate locktimes between chains
# def verify_p2sh(trade):
    # htlc = create_htlc(trade.buy.currency, trade.buy.fulfiller, trade.buy.initiator, trade.commitment, trade.buy.locktime)
    # buyer_p2sh = htlc['p2sh']
    # print("Buyer p2sh:", buyer_p2sh)
    # If the two p2sh match...
    # if buyer_p2sh == trade.buy.p2sh:
    # else:
    #     print("Compiled p2sh for htlc does not match what seller sent.")

def create_htlc(currency, funder, redeemer, commitment, locktime):
    if currency == 'bitcoin':
        sell_p2sh = bitcoinRPC.hashtimelockcontract(funder, redeemer, commitment, locktime)
    elif currency == 'zcash':
        sell_p2sh = zcashRPC.hashtimelockcontract(funder, redeemer, commitment, locktime)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return sell_p2sh

def fund_htlc(currency, p2sh, amount):
    if currency == 'bitcoin':
        txid = bitcoinRPC.fund_htlc(p2sh, amount)
    elif currency == 'zcash':
        txid = zcashRPC.fund_htlc(p2sh, amount)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return txid

def redeem_p2sh(contract, secret):
    currency = contract.currency
    if currency == 'bitcoin':
        res = bitcoinRPC.redeem_contract(contract, secret)
    elif currency == 'zcash':
        res = zcashRPC.redeem_contract(contract, secret)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return res

def refund_contract(contract):
    currency = contract.currency
    if currency == 'bitcoin':
        res = bitcoinRPC.refund(contract)
    elif currency == 'zcash':
        res = zcashRPC.refund(contract)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return res

def parse_secret(currency, txid):
    if currency == 'bitcoin':
        secret = bitcoinRPC.parse_secret(txid)
    elif currency == 'zcash':
        secret = zcashRPC.parse_secret(txid)
    else:
        raise ValueError("Currency not recognized: ", currency)
    return secret

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
    setattr(trade.buy, 'locktime', contract['locktime'])
    save(trade)

def create_buy_p2sh(trade, commitment, locktime):
    ## CREATE BUY CONTRACT
    buy = trade.buy
    print("\nNow creating buy contract on the {0} blockchain where you will wait for the buyer to send funds...".format(buy.currency))
    buy_contract = create_htlc(buy.currency, buy.fulfiller, buy.initiator, commitment, locktime)
    print("Buy contract", buy_contract)

    setattr(trade.buy, 'p2sh', buy_contract['p2sh'])
    setattr(trade.buy, 'redeemScript', buy_contract['redeemScript'])
    setattr(trade.buy, 'redeemblocknum', buy_contract['redeemblocknum'])
    setattr(trade.buy, 'locktime', buy_contract['locktime'])
    print("\nNow contact the buyer and tell them to send funds to this p2sh: {0}\n".format(trade.buy.p2sh))

    save(trade)

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
            secret = bitcoinRPC.parse_secret(trade.buy.redeem_tx)
        else:
            secret = zcashRPC.parse_secret(trade.buy.redeem_tx)
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
        txs = redeem_p2sh(trade.buy, secret)
        print("You have redeemed {0} {1}!".format(buy.amount, buy.currency))
        return txs

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

def initialize_trade(tradeid, **kwargs):
    trade = Trade()
    conf = kwargs['conf']
    if conf == 'cli':
        init_addrs = userInput.get_initiator_addresses()
        fulfill_addrs = userInput.get_fulfiller_addresses()
        amounts = userInput.get_trade_amounts()
        print("AMOUNTS", amounts)
    else:
        init_addrs = ADDRS[conf]['initiator']
        fulfill_addrs = ADDRS[conf]['fulfiller']
        amounts = ADDRS[conf]['amounts']

    sell = amounts['sell']
    buy = amounts['buy']
    sell_currency = sell['currency']
    buy_currency = buy['currency']
    sell['initiator'] = init_addrs[sell_currency]
    buy['initiator'] = init_addrs[buy_currency]
    sell['fulfiller'] = fulfill_addrs[sell_currency]
    buy['fulfiller'] = fulfill_addrs[buy_currency]

    # initializing contract classes with addresses, currencies, and amounts
    trade.sell = Contract(sell)
    trade.buy = Contract(buy)
    print(trade.sell.__dict__)
    print(trade.buy.__dict__)
    return tradeid, trade

def seller_init(tradeid, trade, network):
    secret = generate_password()
    db.save_secret(tradeid, secret)
    print("Generated a secret preimage to lock funds. This will only be stored locally: {0}".format(secret))

    hash_of_secret = sha256(secret)
    # TODO: Implement locktimes and mock block passage of time
    sell_locktime = 20
    buy_locktime = 10 # Must be more than first tx
    print("Creating pay-to-script-hash for sell contract...")

    # create the p2sh addrs
    create_sell_p2sh(trade, hash_of_secret, sell_locktime)
    create_buy_p2sh(trade, hash_of_secret, buy_locktime)

    trade.commitment = b2x(hash_of_secret)
    print("TRADE after seller init: {0}".format(trade.toJSON()))
    return trade
