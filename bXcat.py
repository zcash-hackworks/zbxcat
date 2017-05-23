#!/usr/bin/env python3

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

import bitcoin
import bitcoin.rpc
from bitcoin import SelectParams
from bitcoin.core import b2x, lx, b2lx, x, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from bitcoin.base58 import decode
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret

from utils import *

import zcash
import zcash.rpc
import pprint, json

# SelectParams('testnet')
SelectParams('regtest')
bitcoind = bitcoin.rpc.Proxy()
FEE = 0.001*COIN

zcashd = zcash.rpc.Proxy()

def get_keys(funder_address, redeemer_address):
    fundpubkey = CBitcoinAddress(funder_address)
    redeempubkey = CBitcoinAddress(redeemer_address)
    # fundpubkey = bitcoind.getnewaddress()
    # redeempubkey = bitcoind.getnewaddress()
    return fundpubkey, redeempubkey

def privkey(address):
    bitcoind.dumpprivkey(address)

def hashtimelockcontract(funder, redeemer, secret, locktime):
    funderAddr = CBitcoinAddress(funder)
    redeemerAddr = CBitcoinAddress(redeemer)
    h = sha256(secret)
    blocknum = bitcoind.getblockcount()
    redeemblocknum = blocknum + locktime
    zec_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                                 redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                                 funderAddr, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
    txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
    # Convert the P2SH scriptPubKey to a base58 Bitcoin address
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    p2sh = str(txin_p2sh_address)
    return {'p2sh': p2sh, 'redeemblocknum': redeemblocknum, 'zec_redeemScript': b2x(zec_redeemScript), 'redeemer': redeemer, 'funder': funder}

def fund_htlc(p2sh, amount):
    send_amount = amount*COIN
    fund_txid = bitcoind.sendtoaddress(p2sh, send_amount)
    txid = b2x(lx(b2x(fund_txid)))
    return txid

def check_funds(p2sh):
    bitcoind.importaddress(p2sh, "", false)
    # Get amount in address
    amount = bitcoind.getreceivedbyaddress(p2sh, 0)
    amount = amount/COIN
    return amount

## TODO: FIX search for p2sh in block
def search_p2sh(block, p2sh):
    print("Fetching block...")
    blockdata = bitcoind.getblock(lx(block))
    print("done fetching block")
    txs = blockdata.vtx
    print("txs", txs)
    for tx in txs:
        txhex = b2x(tx.serialize())
        # Using my fork of python-zcashlib to get result of decoderawtransaction
        txhex = txhex + '00'
        rawtx = zcashd.decoderawtransaction(txhex)
        # print('rawtx', rawtx)
        print(rawtx)
        for vout in rawtx['vout']:
            if 'addresses' in vout['scriptPubKey']:
                for addr in vout['scriptPubKey']['addresses']:
                    print("Sent to address:", addr)
                    if addr == p2sh:
                        print("Address to p2sh found in transaction!", addr)
    print("Returning from search_p2sh")


def get_tx_details(txid):
    fund_txinfo = bitcoind.gettransaction(fund_tx)
    return fund_txinfo['details'][0]


   

def redeem(p2sh, action):
    contracts = get_contract()
    trade = get_trade()
    for key in contracts:
        if key == p2sh:
            contract = contracts[key]
    if contract:
        print("Redeeming tx in p2sh", p2sh)
        # TODO: Have to get tx info from saved contract p2sh
        redeemblocknum = contract['redeemblocknum']
        zec_redeemScript = contract['zec_redeemScript']

        txid = trade['action']['fund_tx']
        details = get_tx_details(txid)
        txin = CMutableTxIn(COutPoint(txid, details['vout']))
        redeemPubKey = CBitcoinAddress(contract['redeemer'])
        txout = CMutableTxOut(details['amount'] - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
        # TODO: these things like redeemblocknum should really be properties of a tx class...
        # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
        tx.nLockTime = redeemblocknum
        sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey?
        privkey = bitcoind.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        txin.scriptSig = CScript([sig, privkey.pub, contract['secret'], OP_TRUE, zec_redeemScript])
        print("Redeem tx hex:", b2x(tx.serialize()))

        print("txin.scriptSig", b2x(txin.scriptSig))
        print("txin_scriptPubKey", b2x(txin_scriptPubKey))
        print('tx', tx)
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("script verified, sending raw tx")
        txid = bitcoind.sendrawtransaction(tx)
        print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
    else:
        print("No contract for this p2sh found in database", p2sh)
