from rpc.ZDaemon import *
import argparse, textwrap
import hashlib

# How to prevent this program from having access to local bitcoind or zcashd? Have to just allow it?
# A bit like a GUI wallet that you download, then use as a local app? Running its own instance of zcashd, bitcoind? (bitcoin SPV client possible?)
#
# UI: Seller puts in their address, buyer puts in theirs. (Job of DEX exchange can be to match orders...)
# Interface extracts pubkeys
# Interface determines locktime, and gives seller their "secret redeem code" for their funds (hash preimage)
# Interface creates the HTLC with preimage
# Interface imports address for the redeem script, for buyer, and for seller. (needs access to local zcashd/bitcoind)
# Buyer sends to p2sh address, funding
# Interface checks that it's in wallet, then creates the redeem transaction (rawtx) for buyer and seller
# After set time passes, interface tries to complete the transaction
# If falls through, uses redeem transactions.

zd = ZDaemon(network=TESTNET)

def get_pubkey_from_taddr():
    taddr = raw_input("Enter the taddr you would like to send from: ")
    resp = zd.validateaddress(taddr)
    if resp['pubkey']:
        pubkey = resp['pubkey']
    print "The pubkey for the address you entered is: ", pubkey
    return pubkey

def create_htlc(pubkey, sellerpubkey):
    # UI is going to be opinionated about timelocks, and provide secret for you.
    secret = raw_input("Enter a secret to lock your funds: ")
    # convert to bytes
    secret_bytes = str.encode(secret)
    digest = hashlib.sha256(preimage).digest()
    time = 10
    # need to add this rpc call, assume is running zcashd on zkcp branch
    htlc = zd.createhtlc(pubkey, sellerpubkey, secret_bytes, time)
    return htlc

def import_address(htlc):
    fund_addr = zd.importaddress(htlc['redeemScript'])
    txs = zd.listunspent()
    for tx in txs:
        if tx['address'] == htlc['address']
        return tx['address']


def fund_p2sh(p2sh):
    fund_tx = zd.sendtoaddress(p2sh)
    return fund_tx

def redeem_p2sh(fund_tx):
    for tx in txs:
        if tx['address'] == htlc['address']
        return tx['address']

    return tx['txid'], tx['vout']
    # write this function too
    rawtx = zd.createrawtransaction(txid, vout, selleraddress, amount)
    # Buyer has to sign raw tx


# out of band: sellerpubkey, selleraddress
pubkey = get_pubkey_from_taddr()
# Wait for pubkey from buyer. Assume some messaging layer, or out of band communication, with seller.
htlc = create_htlc(pubkey, sellerpubkey)
# import address for both buyer and seller
addr = import_address(htlc)
# Buyer funds tx
fund_tx = fund_p2sh(addr)
# Now seller must redeem
