#!/usr/bin/env python3

# Based on spend-p2sh-txout.py from python-bitcoinlib.
# Copyright (C) 2014 The python-bitcoinlib developers
# Copyright (C) 2017 The Zcash developers

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

from bitcoin import SelectParams
from bitcoin.core import b2x, lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL
from bitcoin.core.script import OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret

import hashlib
from daemon import *

SelectParams('testnet')

# The parameters needed for the htlc - hash preimage, sender/seller address, recipient/buyer address, num of blocks for timeout
preimage = b'preimage'
h = hashlib.sha256(preimage).digest()
seckey = CBitcoinSecret('cShLodcaVA7JjDXnRaK5jsmQhPJmBDeXPd4Fzx8dRD9ih6gmXKH6')

# AUTOMATE - get recipient addr
recipient_address = get_recipient_address()
print(' recipient_address (newly generated)', recipient_address)
sender_address = get_sender_address()
print(' sender_address (newly generated)', sender_address)

recipientpubkey = CBitcoinAddress('mheZcjatFMjcHX5hVQdAY4Lvxm7q7rXuU2')
senderpubkey = CBitcoinAddress('mheZcjatFMjcHX5hVQdAY4Lvxm7q7rXuU2')

blocknum = 7
# Create a htlc redeemScript. Similar to a scriptPubKey the redeemScript must be
# satisfied for the funds to be spent.
txin_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                             recipientpubkey, OP_ELSE, blocknum, OP_DROP, OP_HASH160,
                             senderpubkey, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
print("redeem script:", b2x(txin_redeemScript))

#print("scriptpubey:", b2x(recipientpubkey.to_scriptPubKey()))

# Create  P2SH scriptPubKey from redeemScript.
txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
print("p2sh_scriptPubKey", b2x(txin_scriptPubKey))

# Convert the P2SH scriptPubKey to a base58 Bitcoin address and print it.
# You'll need to send some funds to it to create a txout to spend.
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
print('Pay to:',str(txin_p2sh_address))

p2sh = str(txin_p2sh_address)

#AUTOMATE funding tx, seller sends funds
amount = 1.0
fund_tx = fund_p2sh(p2sh, amount)
print("TXID", fund_tx)

# AUTOMATE import this address?
importaddress(p2sh)
print('p2sh address imported')

# MINE THE FUNDED TX
generate(1)

print('Now redeeming.........')

# lx() takes *little-endian* hex and converts it to bytes; in Bitcoin
# transaction hashes are shown little-endian rather than the usual big-endian.

# AUTOMATE
txid = lx(fund_tx)
details = tx_details(fund_tx)
print('get details of fund_tx', details)
vout = details['vout']
print('vout', vout)

# Create the txin structure, which includes the outpoint. The scriptSig
# defaults to being empty.
txin = CMutableTxIn(COutPoint(txid, vout))

# Create the txout. This time we create the scriptPubKey from a Bitcoin
# address.
# AUTOMATE: amount and address set above
redeemed = amount*COIN
fee = 0.001*COIN
txout = CMutableTxOut(redeemed - fee, CBitcoinAddress(recipient_address).to_scriptPubKey())

# Create the unsigned transaction.
tx = CMutableTransaction([txin], [txout])

# Calculate the signature hash for that transaction. Note how the script we use
# is the redeemScript, not the scriptPubKey. EvalScript() will be evaluating the redeemScript
sighash = SignatureHash(txin_redeemScript, tx, 0, SIGHASH_ALL)

# Now sign it. We have to append the type of signature we want to the end, in
# this case the usual SIGHASH_ALL.
sig = seckey.sign(sighash) + bytes([SIGHASH_ALL])

# Set the scriptSig of our transaction input appropriately.
txin.scriptSig = CScript([ sig,seckey.pub, preimage, OP_TRUE, txin_redeemScript])

print("scriptSig:", b2x(txin.scriptSig))

# Verify the signature worked.
VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))

# Tx to hex
hextx = b2x(tx.serialize())
print(hextx)

# AUTOMATE: Send raw redeem tx
txid = sendrawtx(hextx)
print("txid of submitted redeem tx", txid)

generate(1)
