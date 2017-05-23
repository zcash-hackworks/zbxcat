#!/usr/bin/env python3

# Based on spend-p2sh-txout.py from python-bitcoinlib.
# Copyright (C) 2017 The Zcash developers

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

import zcash
import zcash.rpc
from zcash import SelectParams
from zcash.core import b2x, lx, x, b2lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from zcash.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from zcash.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from zcash.wallet import CBitcoinAddress, CBitcoinSecret

from utils import *

# SelectParams('testnet')
SelectParams('regtest')
zcashd = zcash.rpc.Proxy()
FEE = 0.001*COIN


def get_keys(funder_address, redeemer_address):
    fundpubkey = CBitcoinAddress(funder_address)
    redeempubkey = CBitcoinAddress(redeemer_address)
    # fundpubkey = zcashd.getnewaddress()
    # redeempubkey = zcashd.getnewaddress()
    return fundpubkey, redeempubkey

def privkey(address):
    zcashd.dumpprivkey(address)

def hashtimelockcontract(funder, redeemer, secret, locktime):
    funderAddr = CBitcoinAddress(funder)
    redeemerAddr = CBitcoinAddress(redeemer)
    h = sha256(secret)
    blocknum = zcashd.getblockcount()
    redeemblocknum = blocknum + locktime
    zec_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                                 redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                                 funderAddr, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
    print("Redeem script for p2sh contract on Zcash blockchain:", b2x(zec_redeemScript))
    txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
    # Convert the P2SH scriptPubKey to a base58 Bitcoin address
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    p2sh = str(txin_p2sh_address)
    # Returning all this to be saved locally in p2sh.json
    return {'p2sh': p2sh, 'redeemblocknum': redeemblocknum, 'zec_redeemScript': b2x(zec_redeemScript), 'redeemer': redeemer, 'funder': funder}

def fund_htlc(p2sh, amount):
    send_amount = amount*COIN
    fund_txid = zcashd.sendtoaddress(p2sh, send_amount)
    txid = b2x(lx(b2x(fund_txid)))
    return txid

def check_funds(p2sh):
    zcashd.importaddress(p2sh, "", False)
    print("Imported address", p2sh)
    # Get amount in address
    amount = zcashd.getreceivedbyaddress(p2sh, 0)
    print("Amount in address", amount)
    amount = amount/COIN
    return amount

def get_tx_details(txid):
    fund_txinfo = zcashd.gettransaction(txid)
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

        txid = trade[action]['fund_tx']
        details = get_tx_details(txid)
        print("Txid for fund tx", txid)
        # must be little endian hex
        txin = CMutableTxIn(COutPoint(lx(txid), details['vout']))
        redeemPubKey = CBitcoinAddress(contract['redeemer'])
        amount = trade[action]['amount'] * COIN
        print("amount: {0}, fee: {1}".format(amount, FEE))
        txout = CMutableTxOut(amount - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
        # TODO: these things like redeemblocknum should really be properties of a tx class...
        # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
        # Is stored as hex, must convert to bytes
        zec_redeemScript = CScript(x(zec_redeemScript))

        tx.nLockTime = redeemblocknum
        sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey?
        privkey = zcashd.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        
        # TODO: Figure out where to store secret preimage securely. Parse from scriptsig of redeemtx
        secret = trade['sell']['secret']
        preimage = secret.encode('utf-8')
        print('preimage', preimage)

        # print('zec_redeemScript', zec_redeemScript)
        txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, zec_redeemScript])
        # print("Redeem tx hex:", b2x(tx.serialize()))

        # Can only call to_p2sh_scriptPubKey on CScript obj
        txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()

        # print("txin.scriptSig", b2x(txin.scriptSig))
        # print("txin_scriptPubKey", b2x(txin_scriptPubKey))
        # print('tx', tx)
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("Script verified, sending raw tx...")
        print("Raw tx of prepared redeem tx: ", b2x(tx.serialize()))
        txid = zcashd.sendrawtransaction(tx)
        txhex = b2x(lx(b2x(txid)))
        print("Txid of submitted redeem tx: ", txhex)
        return txhex
    else:
        print("No contract for this p2sh found in database", p2sh)


def new_zcash_addr():
    addr = zcashd.getnewaddress()
    print('new ZEC addr', addr.to_p2sh_scriptPubKey)
    return addr.to_scriptPubKey()
