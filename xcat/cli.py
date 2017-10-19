import argparse
import textwrap
import subprocess
import os
import logging
from xcat.db import DB
import xcat.userInput as userInput
import xcat.utils as utils
from xcat.protocol import Protocol
from xcat.trades import Trade

class CLI():
    def __init__(self):
        self.db = DB()
        self.protocol = Protocol()

    def checkSellStatus(self, tradeid):
        trade = self.db.get(tradeid)
        status = self.seller_check_status(trade)
        print("Trade status: {0}\n".format(status))

        if status == 'init':
            userInput.authorize_fund_sell(trade)
            fund_tx = self.protocol.fund_sell_contract(trade)

            print("Sent fund_tx", fund_tx)
            trade.sell.fund_tx = fund_tx
            self.db.create(trade, tradeid)

        elif status == 'buyerFunded':
            secret = self.db.get_secret(tradeid)
            print("Retrieved secret to redeem funds for "
                  "{0}: {1}".format(tradeid, secret))
            txs = self.protocol.seller_redeem_p2sh(trade, secret)
            if 'redeem_tx' in txs:
                trade.buy.redeem_tx = txs['redeem_tx']
                print("Redeem tx: ", txs['redeem_tx'])
            if 'refund_tx' in txs:
                trade.buy.redeem_tx = txs['refund_tx']
                print("Buyer refund tx: ", txs['refund_tx'])
                txs = self.protocol.refund_contract(trade.sell)  # Refund to seller
                print("Your refund txid: ", txs['refund_tx'])
            self.db.create(trade, tradeid)
            # Remove from db? Or just from temporary file storage
            utils.cleanup(tradeid)

        elif status == 'sellerFunded':
            print("Buyer has not yet funded the contract where you offered to "
                  "buy {0}, please wait for them to complete "
                  "their part.".format(trade.buy.currency))

        elif status == 'sellerRedeemed':
            print("You have already redeemed the p2sh on the second chain of "
                  "this trade.")


    def buyer_check_status(self, trade):
        sellState = self.protocol.check_fund_status(
            trade.sell.currency, trade.sell.p2sh)
        buyState = self.protocol.check_fund_status(
            trade.buy.currency, trade.buy.p2sh)
        if sellState == 'funded' and buyState == 'empty':
            return 'sellerFunded'  # step1
        # TODO: Find funding txid. How does buyer get seller redeemed tx?
        elif sellState == 'funded' and hasattr(trade.buy, 'fund_tx'):
            return 'sellerRedeemed'  # step3
        elif sellState == 'funded' and buyState == 'funded':
            return 'buyerFunded'  # step2
        elif sellState == 'empty' and buyState == 'empty':
            if hasattr(trade.sell, 'redeem_tx'):
                return 'buyerRedeemed'  # step4
            else:
                return 'init'


    def seller_check_status(self, trade):
        sellState = self.protocol.check_fund_status(
            trade.sell.currency, trade.sell.p2sh)
        buyState = self.protocol.check_fund_status(
            trade.buy.currency, trade.buy.p2sh)
        if sellState == 'funded' and buyState == 'empty':
            return 'sellerFunded'  # step1
        elif sellState == 'funded' and hasattr(trade.buy, 'redeem_tx'):
            return 'sellerRedeemed'  # step3
        # TODO: How does seller get buyer funded tx?
        elif sellState == 'funded' and buyState == 'funded':
            return 'buyerFunded'  # step2
        elif sellState == 'empty' and buyState == 'empty':
            if hasattr(trade.buy, 'redeem_tx'):
                return 'buyerRedeemed'  # step4
            else:
                return 'init'  # step0


    def checkBuyStatus(self, tradeid):
        trade = self.db.get(tradeid)
        status = self.buyer_check_status(trade)
        print("Trade status: {0}\n".format(status))
        if status == 'init':
            print("Trade has not yet started, waiting for seller to fund the "
                  "sell p2sh.")
        elif status == 'buyerRedeemed':
            print("This trade is complete, both sides redeemed.")
        elif status == 'sellerFunded':
            print("One active trade available, fulfilling buyer contract...")
            input("Type 'enter' to allow this program to send funds on your "
                  "behalf.")
            print("Trade commitment", trade.commitment)
            # if verify_p2sh(trade):
            fund_tx = self.protocol.fund_contract(trade.buy)
            print("\nYou sent this funding tx: ", fund_tx)
            trade.buy.fund_tx = fund_tx
            self.db.create(trade, tradeid)
        elif status == 'sellerRedeemed':
            secret = self.protocol.find_secret_from_fundtx(trade.buy.currency,
                                                      trade.buy.p2sh,
                                                      trade.buy.fund_tx)
            if secret is not None:
                print("Found secret on blockchain in seller's redeem tx: ", secret)
                txs = self.protocol.redeem_p2sh(trade.sell, secret)
                if 'redeem_tx' in txs:
                    trade.sell.redeem_tx = txs['redeem_tx']
                    print("Redeem txid: ", trade.sell.redeem_tx)
                elif 'refund_tx' in txs:
                    trade.sell.redeem_tx = txs['refund_tx']
                    print("Refund tx: ", txs['refund_tx'])
                self.db.create(trade, tradeid)
                print("XCAT trade complete!")
            else:
                # Search if tx has been refunded from p2sh
                print("Secret not found in redeemtx")


    # Import a trade in hex, and save to db
    def importtrade(self, tradeid, hexstr=''):
        trade = utils.x2s(hexstr)
        trade = Trade(trade)
        self.protocol.import_addrs(trade)
        print(trade.toJSON())
        self.db.create(trade, tradeid)


    def wormhole_importtrade(self):
        res = subprocess.call('wormhole receive', shell=True)
        if res == 0:
            tradeid = input("Enter filename of received trade data to import "
                            "(printed on line above): ")
            with open(tradeid) as infile:
                hexstr = infile.readline().strip()
            self.importtrade(tradeid, hexstr)
            print("Successfully imported trade using magic-wormhole")
            os.remove(tradeid)
        else:
            print("Importing trade using magic-wormhole failed.")


    # Export a trade by its tradeid
    def exporttrade(self, tradeid, wormhole=False):
        trade = self.db.get(tradeid)
        hexstr = utils.s2x(trade.toJSON())
        if wormhole:
            tradefile = os.path.join(utils.ROOT_DIR, '.tmp/{0}'.format(tradeid))
            print(tradefile)
            with open(tradefile, '+w') as outfile:
                outfile.write(hexstr)
            print("Exporting trade to buyer using magic wormhole.")
            subprocess.call('wormhole send {0}'.format(tradefile), shell=True)
        else:
            print(hexstr)
            return hexstr

    def findtrade(self, tradeid):
        trade = self.db.get(tradeid)
        print(trade.toJSON())
        return trade

    def find_role(self, contract):
        # When regtest created both addrs on same machine, role is both.
        if self.protocol.is_myaddr(contract.initiator):
            if self.protocol.is_myaddr(contract.fulfiller):
                return 'test'
            else:
                return 'initiator'
        else:
            if self.protocol.is_myaddr(contract.fulfiller):
                return 'fulfiller'
            else:
                raise ValueError('You are not a participant in this contract.')


    def checktrade(self, tradeid):
        print("In checktrade")
        trade = self.db.get(tradeid)
        if find_role(trade.sell) == 'test':
            input("Is this a test? Both buyer and seller addresses are yours, "
                  "press 'enter' to test.")
            self.checkSellStatus(tradeid)
            self.checkBuyStatus(tradeid)
            self.checkSellStatus(tradeid)
            self.checkBuyStatus(tradeid)
        elif find_role(trade.sell) == 'initiator':
            print("You are the seller in this trade.")
            # role = 'seller'
            self.checkSellStatus(tradeid)
        else:
            print("You are the buyer in this trade.")
            # role = 'buyer'
            self.checkBuyStatus(tradeid)

    def newtrade(self, tradeid, **kwargs):
        print("Creating new XCAT trade...")
        utils.erase_trade()
        conf = kwargs['conf'] if 'conf' in kwargs else 'regtest'
        network = kwargs['network'] if 'network' in kwargs else 'regtest'
        tradeid, trade = self.protocol.initialize_trade(tradeid, conf=conf, network=network)
        print("New trade created: {0}".format(trade))

        trade, secret = self.protocol.seller_init(tradeid, trade, network=network)
        self.db.save_secret(tradeid, secret)
        print("\nGenerated a secret preimage to lock funds. This will only "
              "be stored locally: {0}".format(secret))
        print("\nUse 'xcat exporttrade [tradeid]' to export the trade and send to the buyer.\n")

        self.db.create(trade, tradeid)
        return trade

    def listtrades(self):
        print("Trades")
        trade_list = self.db.dump()
        for trade in trade_list:
            print("{0}: {1}".format(trade[0], trade[1]))

def main():
    cli = CLI()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
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
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode. Defaults to false")
    parser.add_argument("-w", "--wormhole", action="store_true", help="Transfer trade data through magic-wormhole")
    parser.add_argument("-c", "--conf", action="store", help="Use trade data in conf file ('testnet' or 'regtest'), or pass trade data in on cli as json.")
    parser.add_argument("-n", "--network", action="store", help="Set network to regtest or mainnet. Defaults to testnet while in alpha.")
    # parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")
    args = parser.parse_args()
    print(args)

    if hasattr(args, 'debug'):
        numeric_level = getattr(logging, 'DEBUG', None)
        logging.basicConfig(format='%(levelname)s: %(message)s',
                            level=numeric_level)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s',
                            level='INFO')

    if hasattr(args, 'network'):
        NETWORK = args.network
    else:
        NETWORK = 'testnet'

    command = args.command

    if command == 'importtrade':
        if args.wormhole:
            cli.wormhole_importtrade()
        else:
            if len(args.arguments) != 2:
                utils.throw("Usage: importtrade [tradeid] [hexstring]")
            tradeid = args.arguments[0]
            hexstr = args.arguments[1]
            cli.importtrade(tradeid, hexstr)

    elif command == 'exporttrade':
        if len(args.arguments) < 1:
            utils.throw("Usage: exporttrade [tradeid]")
        tradeid = args.arguments[0]
        cli.exporttrade(tradeid, args.wormhole)

    elif command == "findtrade":
        if len(args.arguments) < 1:
            utils.throw("Usage: findtrade [tradeid]")
        print("Finding trade")
        key = args.arguments[0]
        cli.findtrade(key)

    elif command == 'checktrade':
        if len(args.arguments) < 1:
            utils.throw("Usage: checktrade [tradeid]")
        tradeid = args.arguments[0]
        cli.checktrade(tradeid)

    elif command == 'listtrades':
        cli.listtrades()

    # TODO: function to tell if tradeid already exists for newtrade

    elif command == 'newtrade':
        if len(args.arguments) < 1:
            utils.throw("Usage: newtrade [tradeid]")
        tradeid = args.arguments[0]
        if args.conf is None:
            conf = 'cli'
        else:
            conf = args.conf
        cli.newtrade(tradeid, network=NETWORK, conf=conf)

    elif command == "daemon":
        # TODO: not implemented
        print("Run as daemon process")

    # Ad hoc testing of workflow starts here
    elif command == "step1":
        tradeid = args.arguments[0]
        cli.checkSellStatus(tradeid)
    elif command == "step2":
        tradeid = args.arguments[0]
        cli.checkBuyStatus(tradeid)
    elif command == "step3":
        # cli.protocol.generate(31)
        tradeid = args.arguments[0]
        cli.checkSellStatus(tradeid)
    elif command == "step4":
        # cli.protocol.generate(1)
        tradeid = args.arguments[0]
        cli.checkBuyStatus(tradeid)
