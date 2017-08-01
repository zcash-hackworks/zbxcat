import argparse, textwrap
from xcat.utils import *
import xcat.db as db
import xcat.bitcoinRPC
import xcat.zcashRPC
import xcat.userInput as userInput
from xcat.trades import *
from xcat.protocol import *
import ast

def save_state(trade, tradeid):
    save(trade)
    db.create(trade, tradeid)

def checkSellStatus(tradeid):
    trade = db.get(tradeid)
    if trade.buy.get_status() == 'funded':
        input("Authorize retrieve secret:")
        secret = get_secret()
        print("SECRET found in checksellactions", secret)
        trade = seller_redeem_p2sh(trade, secret)
        print("TRADE SUCCESSFULLY REDEEMED", trade)
        save_state(trade, tradeid)
    elif trade.buy.get_status() == 'empty':
        print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade.buy.currency))
    elif trade.buy.get_status() == 'redeemed':
        print("You have already redeemed the p2sh on the second chain of this trade.")

# TODO: function to calculate appropriate locktimes between chains
def checkBuyStatus(tradeid):
    trade = db.get(tradeid)
    if trade.sell.get_status() == 'redeemed' and trade.buy.get_status() == 'redeemed':
        print("This trade is complete, both sides redeemed.")
    elif trade.sell.get_status() == 'funded' and trade.buy.get_status() != 'redeemed':
        print("One active trade available, fulfilling buyer contract...")
        # they should calculate redeemScript for themselves
        print("Trade commitment", trade.commitment)
        # TODO: which block to start computation from?
        # htlc = create_htlc(trade.buy.currency, trade.buy.fulfiller, trade.buy.initiator, trade.commitment, trade.buy.locktime)
        # buyer_p2sh = htlc['p2sh']
        # print("Buyer p2sh:", buyer_p2sh)
        # If the two p2sh match...
        # if buyer_p2sh == trade.buy.p2sh:
        fund_tx = fund_contract(trade.buy)
        trade.buy.fund_tx = fund_tx
        print("trade buy with redeemscript?", trade.buy.__dict__)
        save_state(trade, tradeid)
        # else:
        #     print("Compiled p2sh for htlc does not match what seller sent.")
    elif trade.buy.get_status() == 'redeemed':
        # TODO: secret parsing
        # secret = parse_secret(trade.buy.currency, trade.buy.redeem_tx)
        secret = get_secret()
        print("Found secret", secret)
        txid = auto_redeem_p2sh(trade.sell, secret)
        print("TXID after buyer redeem", txid)
        print("XCAT trade complete!")

# Import a trade in hex, and save to db
def importtrade(hexstr, tradeid):
    trade = x2s(hexstr)
    trade = db.instantiate(trade)
    save_state(trade, tradeid)

# Export a trade by its tradeid
def exporttrade(tradeid):
    # trade = get_trade()
    trade  = db.get(tradeid)
    hexstr = s2x(trade.toJSON())
    print(hexstr)
    return hexstr

def findtrade(tradeid):
    trade = db.get(tradeid)
    print(trade)
    return trade

def checktrade(tradeid):
    print("In checktrade")
    trade = db.get(tradeid)
    if find_role(trade.sell) == 'test':
        input("Is this a test? Both buyer and seller addresses are yours, press 'enter' to test.")
        checkBuyStatus(tradeid)
        checkSellStatus(tradeid)
        checkBuyStatus(tradeid)
    elif find_role(trade.sell) == 'initiator':
        print("You are the seller in this trade.")
        role = 'seller'
        checkSellStatus(tradeid)
    else:
        print("You are the buyer in this trade.")
        role = 'buyer'
        checkBuyStatus(tradeid)

def newtrade(tradeid):
    erase_trade()
    role = 'seller'
    print("Creating new XCAT trade...")
    trade = seller_init(Trade())
    # Save it to leveldb
    # db.create(trade)
    save_state(trade, tradeid)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent('''\
                == Trades ==
                newtrade "tradeid" - create a new trade
                checktrade "tradeid"- check for actions to be taken on an existing trade
                importtrade "hexstr" - import an existing trade from a hex string
                exporttrade "tradeid" - export the data of an existing trade as a hex string. Takes the tradeid as an argument
                findtrade "tradeid" - find a trade by the tradeid

                '''))
    parser.add_argument("command", action="store", help="list commands")
    parser.add_argument("argument", action="store", nargs="*", help="add an argument")
    # parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")
    # TODO: function to view available trades
    # TODO: function to tell if tradeid already exists for newtrade
    args = parser.parse_args()

    # how to hold state of role
    command = args.command
    if command == 'importtrade':
        hexstr = args.argument[0]
        tradeid = args.argument[1]
        importtrade(hexstr, tradeid)
    elif command == 'exporttrade':
        tradeid = args.argument[0]
        exporttrade(tradeid)
    elif command == "findtrade":
        print("Finding trade")
        key = args.argument[0]
        findtrade(key)
    elif command == 'checktrade':
        tradeid = args.argument[0]
        checktrade(tradeid)
    elif command == 'newtrade':
        print("in new trade")
        try:
            tradeid = args.argument[0]
            newtrade(tradeid)
        except:
            tradeid = userInput.enter_trade_id()
            newtrade(tradeid)
    elif command == "daemon":
        #TODO: implement
        print("Run as daemon process")
    # Ad hoc testing of workflow starts here
    elif command == "step2":
        # trade = get_trade()
        tradeid = args.argument[0]
        checkBuyStatus(tradeid)
    elif command == "step3":
        tradeid = args.argument[0]
        checkSellStatus(tradeid)
    elif command == "step4":
        tradeid = args.argument[0]
        checkBuyStatus(tradeid)
