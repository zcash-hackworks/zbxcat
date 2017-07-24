import argparse, textwrap
from utils import *
import database as db
import bXcat, zXcat
from trades import *
from xcat import *
import ast

def find_role(contract):
    # Obviously when regtest created both addrs on same machine, role is both.
    if parse_addrs(contract.initiator):
        return 'initiator'
    else:
        return 'fulfiller'

def parse_addrs(address):
    if address[:1] == 'm':
        status = bXcat.validateaddress(address)
    else:
        status = zXcat.validateaddress(address)
    status = status['ismine']
    print("Address {0} is mine: {1}".format(address, status))
    return status

def checkSellActions(trade):
    if trade.buy.get_status() == 'funded':
        seller_redeem(trade)
    elif trade.buy.get_status() == 'empty':
        print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade.buy.currency))

def checkBuyActions(trade):
    if trade.sell.get_status() == 'funded' and trade.buy.get_status() != 'redeemed':
        print("One active trade available, fulfilling buyer contract...")
        buyer_fulfill(trade)
    elif trade.buy.get_status() == 'redeemed':
        buyer_redeem(trade)
        print("XCAT trade complete!")

def instantiateTrade(trade):
    return Trade(buy=Contract(trade['buy']), sell=Contract(trade['sell']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent('''\
                == Trades ==
                newtrade - create a new trade
                checktrades - check for actions to be taken on existing trades
                importtrade "hexstr" - import an existing trade from a hex string
                exporttrade - export the data of an existing xcat trade as a hex string
                findtrade - find a trade by the txid of the currency being traded out of

                '''))
    parser.add_argument("command", action="store", help="list commands")
    parser.add_argument("argument", action="store", nargs="*", help="add an argument")
    # parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")
    args = parser.parse_args()

    # how to hold state of role
    command = args.command
    if command == 'importtrade':
        hexstr = args.argument[0]
        trade = x2s(hexstr)
        trade = instantiateTrade(ast.literal_eval(trade))
        db.create(trade)
        # print(trade.toJ)
    elif command == 'exporttrade':
        trade = get_trade()
        hexstr = s2x(str(trade))
        print(trade)
        print(hexstr)
    elif command == 'checktrades':
        trade = get_trade()
        trade = instantiateTrade(trade)
        if find_role(trade.sell) == 'initiator':
            role = 'seller'
            checkSellActions(trade)
        else:
            role = 'buyer'
            checkBuyActions(trade)
    elif command == 'newtrade':
        erase_trade()
        role = 'seller'
        print("Creating new XCAT trade...")
        trade = seller_initiate(Trade())
        # Save it to leveldb
        db.create(trade)
    elif command == "daemon":
        #TODO: implement
        print("Run as daemon process")
    elif command == "findtrade":
        print("Finding trade")
        txid = args.argument[0]
        trade = db.get(txid)
        print(x2s(b2x(trade)))
