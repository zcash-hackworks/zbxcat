#!/usr/bin/env python3

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

import bitcoin
import bitcoin.rpc
from bitcoin import SelectParams
from bitcoin.core import b2x, lx, b2lx, x, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160, CTransaction
from bitcoin.base58 import decode
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, SIGHASH_NONE, SIGHASH_ANYONECANPAY, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE, OP_FALSE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2PKHBitcoinAddress

from xcat.utils import *
import logging

FEE = 0.001*COIN

SelectParams('regtest')
bitcoind = bitcoin.rpc.Proxy()

address = bitcoind.getnewaddress()
print(address)
privkey = bitcoind.dumpprivkey(address)

# Simple CLTV test p2sh
blocknum = bitcoind.getblockcount()
print("Current blocknum on Bitcoin: ", blocknum)
redeemblocknum = blocknum + 1
print("Redeemblocknum on Bitcoin: ", redeemblocknum)

# Script
redeemScript = CScript([redeemblocknum, OP_CHECKLOCKTIMEVERIFY])

print("Redeem script for p2sh contract on Bitcoin blockchain: {0}".format(b2x(redeemScript)))
txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
# Convert the P2SH scriptPubKey to a base58 Bitcoin address
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
p2sh = str(txin_p2sh_address)
# Import address at same time you create
bitcoind.importaddress(p2sh, "", False)

bitcoind.generate(3)
blocknum = bitcoind.getblockcount()
print("Current blocknum on Bitcoin 2: ", blocknum)
print("Redeemblocknum on Bitcoin 2: ", redeemblocknum)

send_amount = float(0.01) * COIN
# Import address at same time that you fund it
bitcoind.importaddress(p2sh, "", False)
fund_txid = bitcoind.sendtoaddress(p2sh, send_amount)
txid = b2x(lx(b2x(fund_txid)))
print("fund txid", txid)

# Find the fund tx...
txs = bitcoind.listunspent()
for tx in txs:
    if tx['address'] == CBitcoinAddress(p2sh):
        print("Found tx to p2sh: {0}".format(p2sh))
        fundtx = tx

# redeemScript = CScript(x(redeemScript))
txin = CMutableTxIn(fundtx['outpoint'])

refundAddr = CBitcoinAddress('mvc56qCEVj6p57xZ5URNC3v7qbatudHQ9b')
txout = CMutableTxOut(fundtx['amount'] - FEE, refundAddr.to_scriptPubKey())
# Create the unsigned raw transaction.
tx = CMutableTransaction([txin], [txout])
# tx.nLockTime = 2430
sighash = bytes(SignatureHash(redeemScript, tx, 0, SIGHASH_NONE))
# privkey = bitcoind.dumpprivkey(refundPubKey)
# sig = privkey.sign(sighash) + bytes([SIGHASH_NONE])
sig = privkey.sign(sighash) + bytes([SIGHASH_NONE])
signed_scriptSig = CScript([sig] + list([SIGHASH_NONE]))

# Sign without secret
# OP_IF, OP_SHA256, commitment, OP_EQUALVERIFY,OP_DUP, OP_HASH160, redeemerAddr,
# OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160, funderAddr,
# OP_ENDIF,
# OP_EQUALVERIFY, OP_CHECKSIG
txin.scriptSig = CScript([signed_scriptSig, redeemScript])
# txin.nSequence = 2185
txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
print('Raw redeem transaction hex: {0}'.format(b2x(tx.serialize())))

res = VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
print("Script verified, sending raw transaction... ", res)
txid = bitcoind.sendrawtransaction(tx)
refund_tx =  b2x(lx(b2x(txid)))
