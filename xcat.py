import zXcat
import bXcat
from utils import *
from waiting import *
from time import sleep
import json
import os, sys
from pprint import pprint
from contract import Contract, Trade, Participant

def check_p2sh(currency, address):
    if currency == 'bitcoin':
        print("Checking funds in Bitcoin p2sh")
        return bXcat.check_funds(address)
    else:
        print("Checking funds in Zcash p2sh")
        return zXcat.check_funds(address)

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
    sell_amt = 3.5
    print(sell_amt)
    buy_amt = input("How much {0} do you want to receive in exchange? ".format(buy_currency))
    buy_amt = 1.2
    print(buy_amt)
    sell = {'currency': sell_currency, 'amount': sell_amt}
    buy = {'currency': buy_currency, 'amount': buy_amt}
    amounts['sell'] = sell
    amounts['buy'] = buy
    return amounts

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

def create_p2sh(htlcTrade):
    currency = htlcTrade.sellContract.currency
    secret = input("Initiating trade: Enter a password to place the {0} you want to sell in escrow: ".format(currency))
    # TODO: hash and store secret only locally.
    if secret == '':
        secret = generate_password()
    print('Remember your password:', secret)
    # Saving secret locally for now
    save_secret(secret)
    # TODO: Implement locktimes and mock block passage of time
    locktime = 20 # Must be more than first tx

    # CREATE SELL CONTRACT
    contract = create_htlc(currency, htlcTrade.sellContract.initiator, htlcTrade.sellContract.fulfiller, secret, locktime)

    contracts = {}
    sell_p2sh = contract['p2sh']
    contracts[contract['p2sh']] = contract
    save_contract(contracts)

    print("sell contract", contract)
    setattr(htlcTrade.sellContract, 'p2sh', contract['p2sh'])
    setattr(htlcTrade.sellContract, 'redeemScript', contract['redeemScript'])
    setattr(htlcTrade.sellContract, 'redeemblocknum', contract['redeemblocknum'])

    print('To complete your sell, send {0} {1} to this p2sh: {2}'.format(htlcTrade.sellContract.amount, currency, htlcTrade.sellContract.p2sh))
    response = input("Type 'enter' to allow this program to send funds on your behalf.")
    print("Sent")

    sell_p2sh = htlcTrade.sellContract.p2sh
    sell_amt = htlcTrade.sellContract.amount
    txid = fund_htlc(currency, sell_p2sh, sell_amt)

    setattr(htlcTrade.sellContract, 'fund_tx', txid)
    # trade['sell']['status'] = 'funded'

    # TODO: Save secret locally for seller
    # setattr(htlcTrade.sellContract, 'secret', secret)

    # TODO: How to cache/save trades locally
    # save_trade(trade)

    ## CREATE BUY CONTRACT
    buy_currency = htlcTrade.buyContract.currency
    buy_initiator = htlcTrade.buyContract.initiator
    buy_fulfiller = htlcTrade.buyContract.fulfiller
    print("Now creating buy contract on the {0} blockchain where you will wait for the buyer to send funds...".format(buy_currency))
    print("HTLC DETAILS", buy_currency, buy_fulfiller, buy_initiator, secret, locktime)
    buy_contract = create_htlc(buy_currency, buy_fulfiller, buy_initiator, secret, locktime)
    print("Buy contract", buy_contract)

    contracts[buy_contract['p2sh']] = buy_contract
    save_contract(contracts)

    setattr(htlcTrade.buyContract, 'p2sh', buy_contract['p2sh'])
    setattr(htlcTrade.buyContract, 'redeemScript', buy_contract['redeemScript'])
    setattr(htlcTrade.buyContract, 'redeemblocknum', buy_contract['redeemblocknum'])
    print("Now contact the buyer and tell them to send funds to this p2sh: ", htlcTrade.buyContract.p2sh)

    save(htlcTrade)
    print_trade(htlcTrade)

def get_initiator_addresses():
    btc_addr = input("Enter your bitcoin address: ")
    # btc_addr = bXcat.new_bitcoin_addr()
    btc_addr = 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp'
    print(btc_addr)
    zec_addr = input("Enter your zcash address: ")
    # zec_addr = zXcat.new_zcash_addr()
    zec_addr = 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'
    print(zec_addr)
    addresses = {'bitcoin': btc_addr, 'zcash': zec_addr}
    return addresses

    # How to be saving the trade to the json file?
    # save_trade(trade)

def get_fulfiller_addresses():
    btc_addr = input("Enter the bitcoin address of the party you want to trade with: ")
    # btc_addr = bXcat.new_bitcoin_addr()
    btc_addr = 'mrQzUGU1dwsWRx5gsKKSDPNtrsP65vCA3Z'
    print(btc_addr)
    zec_addr = input("Enter the zcash address of the party you want to trade with: ")
    # zec_addr = zXcat.new_zcash_addr()
    zec_addr = 'tmTjZSg4pX2Us6V5HttiwFZwj464fD2ZgpY'
    print(zec_addr)
    addresses = {'bitcoin': btc_addr, 'zcash': zec_addr}
    return addresses

def buyer_fulfill(htlcTrade):
    buy_p2sh = htlcTrade.buyContract.p2sh
    sell_p2sh = htlcTrade.sellContract.p2sh
    buy_currency = htlcTrade.buyContract.currency
    sell_currency = htlcTrade.sellContract.currency
    buy_amount = htlcTrade.buyContract.amount
    sell_amount = htlcTrade.sellContract.amount
    buy_p2sh_balance = check_p2sh(buy_currency, buy_p2sh)
    sell_p2sh_balance = check_p2sh(sell_currency, sell_p2sh)

    if buy_p2sh_balance == 0:
        input("The seller's p2sh is funded with {0} {1}, type 'enter' if this is the amount you want to buy in {1}.".format(sell_p2sh_balance, sell_currency))
        input("You have not send funds to the contract to buy {1} (requested amount: {0}), type 'enter' to allow this program to send the agreed upon funds on your behalf.".format(buy_p2sh_balance, buy_currency))
        print("Buy amt,", buy_amount)
        txid = fund_htlc(buy_currency, buy_p2sh, buy_amount)
        print("Fund tx txid:", txid)
        setattr(htlcTrade.buyContract, 'fund_tx', txid)

        save(htlcTrade)
    else:
        print("It looks like you've already funded the contract to buy {1}, the amount in escrow in the p2sh is {0}.".format(buy_p2sh_balance, buy_currency))
        print("Please wait for the seller to remove your funds from escrow to complete the trade.")
    print_trade('buyer')


def check_blocks(p2sh):
    # blocks = []
    with open('watchdata', 'r') as infile:
        for line in infile:
            res = bXcat.search_p2sh(line.strip('\n'), p2sh)
            # blocks.append(line.strip('\n'))
    # print(blocks)
    # for block in blocks:
    #     res = bXcat.search_p2sh(block, p2sh)

def redeem_p2sh(contract, secret):
    currency = contract.currency
    if currency == 'bitcoin':
        res = bXcat.auto_redeem(contract, secret)
    else:
        res = zXcat.auto_redeem(contract, secret)
    return res

# def redeem_p2sh(contract):
#     currency = contract['currency']
#     if currency == 'bitcoin':
#         res = bXcat.redeem(htlcTrade.buyContract)
#     else:
#         res = zXcat.redeem(htlcTrade.buyContract)
#     return res

def seller_redeem(htlcTrade):
    buy_currency = htlcTrade.buyContract.currency
    buy_amount = htlcTrade.buyContract.amount
    buy_p2sh = htlcTrade.buyContract.p2sh
    input("Buyer funded the contract where you offered to buy {0}, type 'enter' to redeem {1} {0} from {2}.".format(buy_currency, buy_amount, buy_p2sh))

    if htlcTrade.sellContract.get_status() == 'redeemed':
        print("You already redeemed the funds and acquired {0} {1}".format(buy_amount, buy_currency))
        exit()
    else:
        # Seller redeems buyer's funded tx (contract in p2sh)
        secret = input("Enter the secret you used to lock the funds in order to redeem:")
        if secret == '':
            secret = get_secret()
        print(secret)
        # txid = redeem_p2sh(htlcTrade.buyContract, secret)
        txid = redeem_p2sh(htlcTrade.buyContract, secret)
        setattr(htlcTrade.buyContract, 'redeem_tx', txid)
        save(htlcTrade)
        print("You have redeemed {0} {1}!".format(buy_amount, buy_currency))
        print_trade('seller')

def buyer_redeem(htlcTrade):
    input("Seller funded the contract where you paid them in {0} to buy {1}, type 'enter' to redeem {2} {1} from {3}.".format(htlcTrade.buyContract.currency, htlcTrade.sellContract.currency, htlcTrade.sellContract.amount, htlcTrade.sellContract.p2sh))
    if htlcTrade.sellContract.get_status() == 'redeemed':
        print("You already redeemed the funds and acquired {0} {1}".format(htlcTrade.sellContract.amount, htlcTrade.sellContract.currency))
        exit()
    else:
        # Buyer redeems seller's funded tx
        p2sh = htlcTrade.sellContract.p2sh
        currency = htlcTrade.sellContract.currency
        # Buy contract is where seller disclosed secret in redeeming
        if htlcTrade.buyContract.currency == 'bitcoin':
            secret = bXcat.parse_secret(htlcTrade.buyContract.redeem_tx)
        else:
            secret = zXcat.parse_secret(htlcTrade.buyContract.redeem_tx)
        print("Found secret in seller's redeem tx", secret)
        redeem_tx = redeem_p2sh(htlcTrade.sellContract, secret)
        setattr(htlcTrade.sellContract, 'redeem_tx', redeem_tx)
        save(htlcTrade)
    exit()


def print_trade(role):
    print("\nTrade status for {0}:".format(role))
    trade = get_trade()
    pprint(trade)

## Main functions determining user workflow
def seller_initiate(trade):
    # Collect or negotiate these participants and amounts any way
    amounts = get_trade_amounts()
    sell = amounts['sell']
    buy = amounts['buy']
    sell_currency = sell['currency']
    buy_currency = buy['currency']
    init_addrs = get_initiator_addresses()
    sell['initiator'] = init_addrs[sell_currency]
    buy['initiator'] = init_addrs[buy_currency]
    fulfill_addrs = get_fulfiller_addresses()
    sell['fulfiller'] = fulfill_addrs[sell_currency]
    buy['fulfiller'] = fulfill_addrs[buy_currency]
    # initializing contract classes with addresses, currencies, and amounts
    htlcTrade.sellContract = Contract(sell)
    htlcTrade.buyContract = Contract(buy)
    print(htlcTrade.sellContract.__dict__)
    print(htlcTrade.buyContract.__dict__)

    create_p2sh(htlcTrade)
    exit()

if __name__ == '__main__':
    print("ZEC <-> BTC XCAT (Cross-Chain Atomic Transactions)")
    print("=" * 50)
    # TODO: Get trade indicated by id number
    # TODO: pass trade into functions?
    # TODO: workflow framed as currency you're trading out of being sell. appropriate?
    # Have initiator propose amounts to trade
    trade = get_trade()

    if trade == None:
        htlcTrade = Trade()
        print("New empty trade")
    else:
        buyContract = Contract(trade['buy'])
        sellContract = Contract(trade['sell'])
        htlcTrade = Trade(buyContract=buyContract, sellContract=sellContract)

    # print("status", trade.sellContract.get_status())

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
            print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade['buy']['currency']))
    else:
        # Need better way of preventing buyer from having secret
        # if 'status' not in trade['buy'] and trade['sell']['status'] == 'funded':
        if htlcTrade.sellContract.get_status() == 'funded' and htlcTrade.buyContract.get_status() != 'redeemed':
            print("One active trade available, fulfilling buyer contract...")
            print(htlcTrade.buyContract.get_status())
            print(htlcTrade.sellContract.get_status())
            buyer_fulfill(htlcTrade)
            # How to monitor if txs are included in blocks -- should use blocknotify and a monitor daemon?
            # p2sh = trade['buy']['p2sh']
            # check_blocks(p2sh)
        elif htlcTrade.buyContract.get_status() == 'redeemed':
            # Seller has redeemed buyer's tx, buyer can now redeem.
            buyer_redeem(htlcTrade)
            print("XCAT trade complete!")



        # Note: there is some little endian weirdness in the bXcat and zXcat files, need to handle the endianness of txids better & more consistently
