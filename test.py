from xcat import *

htlcTrade = Trade()
print("Starting test of xcat...")

def get_initiator_addresses():
    return {'bitcoin': 'myfFr5twPYNwgeXyjCmGcrzXtCmfmWXKYp', 'zcash': 'tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'}

def get_fulfiller_addresses():
    return {'bitcoin': 'mrQzUGU1dwsWRx5gsKKSDPNtrsP65vCA3Z', 'zcash': 'tmTjZSg4pX2Us6V5HttiwFZwj464fD2ZgpY'}

def initiate(trade):
    # Get amounts
    amounts = {"sell": {"currency": "bitcoin", "amount": "0.5"}, "buy": {"currency": "zcash", "amount": "1.12"}}
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
    locktime = 20 # Must be more than first tx

    create_sell_p2sh(trade, secret, locktime)
    txid = fund_sell_contract(trade)
    print("Sent")
    create_buy_p2sh(trade, secret, locktime)

def fulfill(trade):
    buy = trade.buyContract
    sell = trade.sellContract
    buy_p2sh_balance = check_p2sh(buy.currency, buy.p2sh)
    sell_p2sh_balance = check_p2sh(sell.currency, sell.p2sh)

    if buy_p2sh_balance == 0:
        print("Buy amt:", buy.amount)
        txid = fund_buy_contract(trade)
        print("Fund tx txid:", txid)
    else:
        raise ValueError("Sell p2sh not funded, buyer cannot redeem")

def redeem_one(trade):
    buy = trade.buyContract
    if trade.sellContract.get_status() == 'redeemed':
        raise RuntimeError("Sell contract status was already redeemed before seller could redeem buyer's tx")
    else:
        secret = get_secret()
        print("GETTING SECRET IN TEST:", secret)
        txid = redeem_p2sh(trade.buyContract, secret)
        print("TX SUCCESSFULLY REDEEMED")
        setattr(trade.buyContract, 'redeem_tx', txid)
        save(trade)
        print("You have redeemed {0} {1}!".format(buy.amount, buy.currency))

def redeem_two(trade):
    if trade.sellContract.get_status() == 'redeemed':
        raise RuntimeError("Sell contract was redeemed before buyer could retrieve funds")
    else:
        # Buy contract is where seller disclosed secret in redeeming
        if trade.buyContract.currency == 'bitcoin':
            secret = bXcat.parse_secret(trade.buyContract.redeem_tx)
        else:
            secret = zXcat.parse_secret(trade.buyContract.redeem_tx)
        print("Found secret in seller's redeem tx", secret)
        redeem_tx = redeem_p2sh(trade.sellContract, secret)
        setattr(trade.sellContract, 'redeem_tx', redeem_tx)
        save(trade)

initiate(htlcTrade)
fulfill(htlcTrade)
redeem_one(htlcTrade)
redeem_two(htlcTrade)

# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))
