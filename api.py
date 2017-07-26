import zXcat
import bXcat
from xcat import *
from zcash.core import b2x
print("Starting test of xcat...")

def get_initiator_addresses():
    baddr = bXcat.new_bitcoin_addr()
    zaddr = zXcat.new_zcash_addr()
    # print("type baddr", type(baddr))
    # print("type baddr", type(baddr.to_scriptPubKey()))
    #return {'bitcoin': baddr.__str__(), 'zcash': zaddr.__str__()}
    return {'bitcoin': 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp', 'zcash': 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'}

def get_fulfiller_addresses():
    baddr = bXcat.new_bitcoin_addr()
    zaddr = zXcat.new_zcash_addr()
    return {'bitcoin': baddr.__str__(), 'zcash': zaddr.__str__()}
    # return {'bitcoin': 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp', 'zcash': 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'}
    # return {'bitcoin': 'mrQzUGU1dwsWRx5gsKKSDPNtrsP65vCA3Z', 'zcash': 'tmTjZSg4pX2Us6V5HttiwFZwj464fD2ZgpY'}






def seller_init():
    print("SELLER INITIATING CONTRACTS")
    print("======+====================")
    trade = get_init()
    # Get amounts
    amounts = {"sell": {"currency": "bitcoin", "amount": "0.01"}, "buy": {"currency": "zcash", "amount": "0.01"}}
    sell = amounts['sell']
    buy = amounts['buy']
    sell_currency = sell['currency']
    buy_currency = buy['currency']
    # Get addresses
    sell['funder'] = trade.sellContract.funder 
    buy['funder'] = trade.buyContract.funder 
    sell['redeemer'] = trade.sellContract.redeemer
    buy['redeemer'] = trade.buyContract.redeemer
    # initializing contract classes with addresses, currencies, and amounts
    trade.sellContract = Contract(sell)
    trade.buyContract = Contract(buy)
    print(trade.sellContract.__dict__)
    print(trade.buyContract.__dict__)
    sell = trade.sellContract
    buy = trade.buyContract
    secret = generate_password()
    hash_of_secret = sha256(secret)
    print("Generating secret to lock funds:", secret)
    save_secret(secret)
    # TODO: Implement locktimes and mock block passage of time
    seller_lock_increment = 100 # Must be more than buyer_locktime, so that seller reveal secret before their own locktime. Currently assuming seller is bitcoin side. If seller is Zcash side this number needs
                            
    buyer_lock_increment = 50
    sell.redeemblocknum= compute_redeemblocknum(sell.currency, seller_lock_increment)
    buy.redeemblocknum = compute_redeemblocknum(buy.currency, buyer_lock_increment)
    sell.hash_of_secret = b2x(hash_of_secret)
    buy.hash_of_secret = b2x(hash_of_secret)
   
    sell = create_and_import_p2sh(sell)
    buy = create_and_import_p2sh(buy)
    sell.hash_of_secret = b2x(hash_of_secret)
    buy.hash_of_secret = b2x(hash_of_secret)

    trade.sellContract = sell
    trade.buyContract = buy

    save_init(trade)
    return trade

def buyer_init():
    print("BUYER INITIATING CONTRACTS")
    print("==========================")
    trade = get_init()
    trade.sellContract = create_and_import_p2sh(trade.sellContract)
    trade.buyContract = create_and_import_p2sh(trade.buyContract)
    save_buyer_trade(trade)


def seller_fund():
    print("SELLER FUNDING SELL CONTRACT")
    print("============================")
    trade = get_init()
    trade.sellContract = fund_contract(trade.sellContract)
    print("fund txid on ", trade.sellContract.currency, " chain is ", trade.sellContract.fund_tx)
    save_seller_trade(trade)

def buyer_fund():
    print("BUYER FUNDING BUY CONTRACT")
    print("==========================")
    trade = get_init() 
    sell = trade.sellContract
    # first check that seller funded as they should 
    sell_p2sh_balance = check_p2sh(sell.currency, sell.p2sh)
    if (sell_p2sh_balance < float(sell.amount)):
                raise ValueError("Sell p2sh not funded, buyer cannot redeem")
    trade.buyContract = fund_contract(trade.buyContract)
    print("fund txid on ", trade.buyContract.currency, " chain is ", trade.buyContract.fund_tx)

    save_buyer_trade(trade)
    
    

def seller_redeem_before_signature():
    trade = get_seller_trade()
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
    

def buyer_redeem():
    print("BUYER REDEEMING SELL CONTRACT")
    print("=============================")
    trade = get_buyer_trade()
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

