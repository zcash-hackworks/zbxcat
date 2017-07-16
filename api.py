import zXcat
import bXcat
from xcat import *

print("Starting test of xcat...")

def get_initiator_addresses():
    baddr = bXcat.new_bitcoin_addr()
    zaddr = zXcat.new_zcash_addr()
    # print("type baddr", type(baddr))
    # print("type baddr", type(baddr.to_scriptPubKey()))
    return {'bitcoin': baddr.__str__(), 'zcash': zaddr.__str__()}
    # return {'bitcoin': 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp', 'zcash': 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'}

def get_fulfiller_addresses():
    baddr = bXcat.new_bitcoin_addr()
    zaddr = zXcat.new_zcash_addr()
    return {'bitcoin': baddr.__str__(), 'zcash': zaddr.__str__()}
    # return {'bitcoin': 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp', 'zcash': 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'}
    # return {'bitcoin': 'mrQzUGU1dwsWRx5gsKKSDPNtrsP65vCA3Z', 'zcash': 'tmTjZSg4pX2Us6V5HttiwFZwj464fD2ZgpY'}

def initiate():
    print("SELLER FUNDING SELL CONTRACT")
    print("============================")
    trade = Trade()
    # Get amounts
    amounts = {"sell": {"currency": "bitcoin", "amount": "0.01"}, "buy": {"currency": "zcash", "amount": "1.12"}}
    sell = amounts['sell']
    buy = amounts['buy']
    sell_currency = sell['currency']
    buy_currency = buy['currency']
    # Get addresses
    init_addrs = get_initiator_addresses()
    sell['initiator'] = init_addrs[sell_currency]
    buy['initiator'] = init_addrs[buy_currency]
    fulfill_addrs = get_fulfiller_addresses()
    sell['fulfiller'] = fulfill_addrs[sell_currency]
    buy['fulfiller'] = fulfill_addrs[buy_currency]
    # initializing contract classes with addresses, currencies, and amounts
    trade.sellContract = Contract(sell)
    trade.buyContract = Contract(buy)
    print(trade.sellContract.__dict__)
    print(trade.buyContract.__dict__)

    secret = generate_password()
    print("Generating secret to lock funds:", secret)
    save_secret(secret)
    # TODO: Implement locktimes and mock block passage of time
    seller_locktime = 6 # Must be more than buyer_locktime, so that seller reveal secret before their own locktime
    buyer_locktime = 3 

    create_sell_p2sh(trade, secret, seller_locktime)
    txid = fund_sell_contract(trade)
    print("Sent fund tx of sell contract:", txid)
    create_buy_p2sh(trade, secret, buyer_locktime)
    save(trade)
    return trade

# buyer checks that seller funded the sell contract, and if so funds the buy contract
def fund_buyer():
    print("BUYER FUNDING BUY CONTRACT")
    print("==========================")
    trade = get_trade()
    buy = trade.buyContract
    sell = trade.sellContract
    # buy_p2sh_balance = check_p2sh(buy.currency, buy.p2sh)
    sell_p2sh_balance = check_p2sh(sell.currency, sell.p2sh)
    if (sell_p2sh_balance < float(sell.amount)):
                raise ValueError("Sell p2sh not funded, buyer cannot redeem")
    print("Seller has deposited funds, so funding the buy contract:")
    txid = fund_buy_contract(trade)
    print("Buyer Fund tx txid:", txid)

def redeem_seller():
    trade = get_trade()
    print(trade)
    print("SELLER REDEEMING BUY CONTRACT")
    print("=============================")
    buy = trade.buyContract
    print(buy)
    # if trade.sellContract.get_status() == 'redeemed':
    #    raise RuntimeError("Sell contract status was already redeemed before seller could redeem buyer's tx")
    #else:
    secret = get_secret() # Just the seller getting his local copy of the secret
    print("SELLER SECRET IN TEST:", secret)
    txid =  redeem_p2sh(trade.buyContract, secret, trade.sellContract)
    setattr(trade.buyContract, 'redeem_tx', txid)
    save(trade)
    

def redeem_buyer():
    print("BUYER REDEEMING SELL CONTRACT")
    print("=============================")
    trade = get_trade()
    buyContract = trade.buyContract
    sellContract = trade.sellContract
    secret = ""
    # if sellContract.get_status() == 'redeemed':
    #     raise RuntimeError("Sell contract was redeemed before buyer could retrieve funds")
    # elif buyContract.get_status() == 'refunded':
    #     print("buyContract was refunded to buyer")
    # else:
    # Buy contract is where seller disclosed secret in redeeming
    if buyContract.currency == 'bitcoin':
        if (bXcat.still_locked(buyContract)):
            if(not hasattr(buyContract,'fund_tx')):
                print("Seems address has not been funded yet. Aborting.")
                quit()
            secret = bXcat.find_secret(buyContract.p2sh,buyContract.fund_tx)
            if(secret != ""):
                print("Found secret in seller's redeem tx on bitcoin chain:", secret)
    else:
        if zXcat.still_locked(buyContract):
            secret = zXcat.find_secret(buyContract.p2sh,buyContract.fund_tx)
            if(secret != ""):
                print("Found secret in seller's redeem tx on zcash chain:", secret)
    redeem_tx = redeem_p2sh(sellContract, secret, buyContract)
    setattr(trade.sellContract, 'redeem_tx', redeem_tx)
    save(trade)


def generate_blocks(num):
    bXcat.generate(num)
    zXcat.generate(num)

