import argparse, textwrap
from utils import *
import database as db
import bXcat, zXcat
from trades import *
from xcat import *

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
    if trade.buyContract.get_status() == 'funded':
        seller_redeem(trade)
    elif trade.buyContract.get_status() == 'empty':
        print("Buyer has not yet funded the contract where you offered to buy {0}, please wait for them to complete their part.".format(trade.buyContract.currency))

def checkBuyActions(trade):
    if trade.sellContract.get_status() == 'funded' and trade.buyContract.get_status() != 'redeemed':
        print("One active trade available, fulfilling buyer contract...")
        buyer_fulfill(trade)
    elif trade.buyContract.get_status() == 'redeemed':
        buyer_redeem(trade)
        print("XCAT trade complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent('''\
                == Contracts ==
                newtrade - create a new trade
                checktrades - check for actions to be taken on existing trades
                importcontract "hexstr" - import an existing trade from a hex string
                exportcontract - (not implemented) export the data of an existing xcat trade as a hex string

                '''))
    parser.add_argument("command", action="store", help="list commands")
    # parser.add_argument("-importcontract", type=str, action="store", help="import an existing trade from a hex string.")
    # parser.add_argument("-newtrade", action="store", help="create a new trade.")
    # parser.add_argument("-checktrades", action="store", help="check status of existing trades")
    args = parser.parse_args()

    # how to hold state of role
    command = args.command
    if command == 'importcontract':
        erase_trade()
        role = 'seller'
        htlcTrade = Trade()
        print("Creating new XCAT transaction...")
    elif command == 'checktrades':
        trade = get_trade()
        buyContract = Contract(trade['buy'])
        sellContract = Contract(trade['sell'])
        trade = Trade(buyContract=buyContract, sellContract=sellContract)
        if find_role(sellContract) == 'initiator':
            role = 'seller'
            checkSellActions(trade)
        else:
            role = 'buyer'
            checkBuyActions(trade)
    elif command == 'newtrade':
        hexstr = args.importcontract
        db.create(hexstr)
