from xcat.utils import *
from xcat.db import *

def enter_trade_id():
    tradeid = input("Enter a unique identifier for this trade: ")
    return tradeid

def get_trade_amounts():
    amounts = {}
    sell_currency = input("Which currency would you like to trade out of (bitcoin or zcash)? ")
    if sell_currency == '':
        sell_currency = 'bitcoin'
    if sell_currency == 'bitcoin':
        buy_currency = 'zcash'
    else:
        buy_currency = 'bitcoin'
    print(sell_currency)
    sell_amt = input("How much {0} do you want to sell? ".format(sell_currency))
    sell_amt = 0.01
    print(sell_amt)
    buy_amt = input("How much {0} do you want to receive in exchange? ".format(buy_currency))
    buy_amt = 0.02
    print(buy_amt)
    sell = {'currency': sell_currency, 'amount': sell_amt}
    buy = {'currency': buy_currency, 'amount': buy_amt}
    amounts['sell'] = sell
    amounts['buy'] = buy
    return amounts

def authorize_fund_sell(htlcTrade):
    print('To complete your sell, send {0} {1} to this p2sh: {2}'.format(htlcTrade.sell.amount, htlcTrade.sell.currency, htlcTrade.sell.p2sh))
    response = input("Type 'enter' to allow this program to send funds on your behalf.")

def get_initiator_addresses():
    btc_addr = input("Enter your bitcoin address or press enter to generate one: ")
    btc_addr = bitcoinRPC.new_bitcoin_addr()
    # btc_addr = 'mgRG44X4PQC1ZCA4V654UZjJGJ3pxbApj2'
    print(btc_addr)
    zec_addr = input("Enter your zcash address or press enter to generate one: ")
    zec_addr = zcashRPC.new_zcash_addr()
    # zec_addr = 'tmLZu7MdjNdA6vbPTNTwdsZo91LnnrVTYB5'
    print(zec_addr)
    addresses = {'bitcoin': btc_addr, 'zcash': zec_addr}
    return addresses

def get_fulfiller_addresses():
    btc_addr = input("Enter the bitcoin address of the party you want to trade with: ")
    # btc_addr = bXcat.new_bitcoin_addr()
    if btc_addr == '':
        btc_addr = "mvc56qCEVj6p57xZ5URNC3v7qbatudHQ9b" # regtest
    print(btc_addr)
    zec_addr = input("Enter the zcash address of the party you want to trade with: ")
    if zec_addr == '':
        zec_addr = "tmTF7LMLjvEsGdcepWPUsh4vgJNrKMWwEyc" # regtest
    # zec_addr = zXcat.new_zcash_addr()
    print(zec_addr)
    addresses = {'bitcoin': btc_addr, 'zcash': zec_addr}
    return addresses

def authorize_buyer_fulfill(sell_p2sh_balance, sell_currency, buy_p2sh_balance, buy_currency):
    input("The seller's p2sh is funded with {0} {1}, type 'enter' if this is the amount you want to buy in {1}.".format(sell_p2sh_balance, sell_currency))
    input("You have not send funds to the contract to buy {1} (requested amount: {0}), type 'enter' to allow this program to send the agreed upon funds on your behalf.".format(buy_p2sh_balance, buy_currency))

def authorize_seller_redeem(buy):
    input("Buyer funded the contract where you offered to buy {0}, type 'enter' to redeem {1} {0} from {2}.".format(buy.currency, buy.amount, buy.p2sh))

def authorize_buyer_redeem(trade):
    input("Seller funded the contract where you paid them in {0} to buy {1}, type 'enter' to redeem {2} {1} from {3}.".format(trade.buy.currency, trade.sell.currency, trade.sell.amount, trade.sell.p2sh))
