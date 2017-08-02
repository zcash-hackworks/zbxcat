import argparse, textwrap
from xcat.utils import *
import xcat.db as db
import xcat.bitcoinRPC
import xcat.zcashRPC
import xcat.userInput as userInput
from xcat.trades import *
from xcat.protocol import *
import ast
import subprocess

def save_state(trade, tradeid):
    save(trade)
    db.create(trade, tradeid)

def checkSellStatus(tradeid):
    trade = db.get(tradeid)
    status = seller_check_status(trade)
    print("In checkSellStatus", status)
    # if trade.buy.get_status() == 'funded':
    if status == 'initFund':
        userInput.authorize_fund_sell(trade)
        fund_tx = fund_sell_contract(trade)
        print("Sent fund_tx", fund_tx)
        trade.sell.fund_tx = fund_tx
        save_state(trade, tradeid)
    elif status == 'buyerFunded':
        secret = userInput.retrieve_password()
        print("SECRET found in checksellactions", secret)
        txs = seller_redeem_p2sh(trade, secret)
        print("TXS IN SELLER REDEEM BUYER TX", txs)
        trade.buy.redeem_tx = txs['redeem_tx']
        print("TRADE SUCCESSFULLY REDEEMED", trade)
        save_state(trade, tradeid)
    # elif trade.buy.get_status() == 'empty':
    elif status == 'sellerFunded':
        print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade.buy.currency))
    # elif trade.buy.get_status() == 'redeemed':
    elif status == 'sellerRedeemed':
        print("You have already redeemed the p2sh on the second chain of this trade.")

def buyer_check_status(trade):
    sellState = check_fund_status(trade.sell.currency, trade.sell.p2sh)
    buyState = check_fund_status(trade.buy.currency, trade.buy.p2sh)
    if sellState == 'funded' and buyState == 'empty':
        return 'sellerFunded' # step1
    # TODO: Find funding txid. How does buyer get seller redeemed tx?
    elif sellState == 'funded' and hasattr(trade.buy, 'fund_tx'):
        return 'sellerRedeemed' # step3
    elif sellState == 'funded' and buyState == 'funded':
        return 'buyerFunded' # step2
    elif sellState == 'empty' and buyState == 'empty':
        return 'buyerRedeemed' # step4

def seller_check_status(trade):
    sellState = check_fund_status(trade.sell.currency, trade.sell.p2sh)
    buyState = check_fund_status(trade.buy.currency, trade.buy.p2sh)
    if sellState == 'funded' and buyState == 'empty':
        return 'sellerFunded' # step1
    elif sellState == 'funded' and hasattr(trade.buy, 'redeem_tx'):
        return 'sellerRedeemed' # step3
    # TODO: How does seller get buyer funded tx?
    elif sellState == 'funded' and buyState == 'funded':
        return 'buyerFunded' # step2
    elif sellState == 'empty' and buyState == 'empty':
        if hasattr(trade.buy, 'redeem_tx'):
            return 'buyerRedeemed' # step4
        else:
            return 'initFund' # step0

# TODO: function to calculate appropriate locktimes between chains
def checkBuyStatus(tradeid):
    trade = db.get(tradeid)
    status = buyer_check_status(trade)
    print("In checkBuyStatus", status)
    if status == 'buyerRedeemed':
        print("This trade is complete, both sides redeemed.")
    # elif trade.sell.get_status() == 'funded' and trade.buy.get_status() != 'redeemed':
    elif status == 'sellerFunded':
        print("One active trade available, fulfilling buyer contract...")
        print("Trade commitment", trade.commitment)
        # htlc = create_htlc(trade.buy.currency, trade.buy.fulfiller, trade.buy.initiator, trade.commitment, trade.buy.locktime)
        # buyer_p2sh = htlc['p2sh']
        # print("Buyer p2sh:", buyer_p2sh)
        # If the two p2sh match...
        # if buyer_p2sh == trade.buy.p2sh:
        fund_tx = fund_contract(trade.buy)
        print("Fund tx coming back in cli", fund_tx)
        trade.buy.fund_tx = fund_tx
        save_state(trade, tradeid)
        # else:
        #     print("Compiled p2sh for htlc does not match what seller sent.")
    elif status == 'sellerRedeemed':
        print("FUND TX CLI", trade.buy.fund_tx)
        secret = find_secret_from_fundtx(trade.buy.currency, trade.buy.p2sh, trade.buy.fund_tx)
        print("Secret in cli", secret)
        # secret = parse_secret(trade.buy.currency, trade.buy.redeem_tx)
        if secret != None:
            print("Found secret", secret)
            txs = redeem_p2sh(trade.sell, secret)
            print("TXS IN SELLER REDEEMED", txs)
            # trade.sell.fund_tx = txs['fund_tx']
            trade.sell.redeem_tx = txs['redeem_tx']
            print("TXID after buyer redeem", trade.sell.redeem_tx)
            save_state(trade, tradeid)
            print("XCAT trade complete!")
        else:
            print("Secret not found in redeemtx")

# Import a trade in hex, and save to db
def importtrade(tradeid, hexstr=''):
    trade = x2s(hexstr)
    trade = db.instantiate(trade)
    import_addrs(trade)
    print(trade.toJSON())
    save_state(trade, tradeid)

def wormhole_importtrade():
    res = subprocess.call('wormhole receive', shell=True)
    if res == 0:
        tradeid = input("Enter filename of received trade data to import (printed on line above): ")
        with open(tradeid) as infile:
            hexstr = infile.readline().strip()
        importtrade(tradeid, hexstr)
        print("Successfully imported trade using magic-wormhole")
        os.remove(tradeid)
    else:
        print("Importing trade using magic-wormhole failed.")

# Export a trade by its tradeid
def exporttrade(tradeid, wormhole=False):
    trade  = db.get(tradeid)
    hexstr = s2x(trade.toJSON())
    if wormhole:
        tradefile = os.path.join(root_dir, '.tmp/{0}'.format(tradeid))
        with open(tradefile, '+w') as outfile:
            outfile.write(hexstr)
        print("Exporting trade to buyer using magic wormhole.")
        subprocess.call('wormhole', 'send', tradefile)
    else:
        print(hexstr)
        return hexstr

def findtrade(tradeid):
    trade = db.get(tradeid)
    print(trade.toJSON())
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
    print("Use 'xcat exporttrade <tradeid> to export the trade and sent to the buyer.'")
    save_state(trade, tradeid)

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
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
    parser.add_argument("arguments", action="store", nargs="*", help="add arguments")
    parser.add_argument("-w", "--wormhole", action="store_true", help="Transfer trade data through magic-wormhole")
    # parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")
    # TODO: function to view available trades
    # TODO: function to tell if tradeid already exists for newtrade
    args = parser.parse_args()

    # how to hold state of role
    command = args.command
    if command == 'importtrade':
        if args.wormhole:
            wormhole_importtrade()
        else:
            if len(args.argument) != 2:
                print("Usage: importtrade [tradeid] [hexstring]")
                exit()
            tradeid = args.argument[0]
            hexstr = args.argument[1]
            importtrade(tradeid, hexstr)
    elif command == 'exporttrade':
        tradeid = args.argument[0]
        exporttrade(tradeid, args.wormhole)
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
    elif command == "step1":
        tradeid = args.argument[0]
        checkSellStatus(tradeid)
    elif command == "step2":
        # trade = get_trade()
        tradeid = args.argument[0]
        checkBuyStatus(tradeid)
    elif command == "step3":
        tradeid = args.argument[0]
        checkSellStatus(tradeid)
    # TODO: When trade finishes, delete wormhole file in tmp dir.
    elif command == "step4":
        tradeid = args.argument[0]
        checkBuyStatus(tradeid)
