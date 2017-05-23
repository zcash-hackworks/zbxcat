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
from zcash.core import b2x, lx, b2lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
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
    print("TX2 Redeem script on Zcash blockchain:", b2x(zec_redeemScript))
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
    print("In zXcat check funds")
    zcashd.importaddress(p2sh, "", false)
    print("Imported address", p2sh)
    # Get amount in address
    amount = zcashd.getreceivedbyaddress(p2sh, 0)
    print("Amount in address", amount)
    amount = amount/COIN
    return amount

def redeem(redeemer, secret, txid):
    print("redeeming tx")
    txin = CMutableTxIn(COutPoint(fund_tx, fund_vout))
    txout = CMutableTxOut(send_amount - FEE, bobpubkey.to_scriptPubKey())
    # Create the unsigned raw transaction.
    tx = CMutableTransaction([txin], [txout])
    # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
    # TODO: these things like redeemblocknum should really be properties of a tx class...
    # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
    tx.nLockTime = redeemblocknum
    sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
    sig = bob_seckey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, bob_seckey.pub, preimage, OP_TRUE, zec_redeemScript])
    print("Redeem tx hex:", b2x(tx.serialize()))

    print("txin.scriptSig", b2x(txin.scriptSig))
    print("txin_scriptPubKey", b2x(txin_scriptPubKey))
    print('tx', tx)
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))

    txid = zcashd.sendrawtransaction(tx)
    print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
