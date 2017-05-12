#!/usr/bin/env python3

# Copyright (C) 2017 the python-zcashlib developers

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

import zcash
import zcash.rpc
from zcash import SelectParams
from zcash.core import b2x, lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from zcash.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_DROP, OP_ENDIF, OP_HASH160, OP_SHA256, OP_EQUAL, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, SIGHASH_ANYONECANPAY, OP_TRUE
from zcash.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from zcash.wallet import CBitcoinAddress, CBitcoinSecret
import hashlib

SelectParams('regtest')
proxy = zcash.rpc.Proxy()

# The parameters needed for the htlc - hash preimage, sender/seller address, recipient/buyer address, num of blocks for timeout
preimage = b'preimage'
h = hashlib.sha256(preimage).digest()

# proxy.getnewaddress() returns CBitcoinAddress
recipientpubkey = proxy.getnewaddress()
senderpubkey = proxy.getnewaddress()
# privkey of the recipient, used to sign the redeemTx
seckey = proxy.dumpprivkey(recipientpubkey)

blocknum = 7
# Create a htlc redeemScript. Similar to a scriptPubKey the redeemScript must be
# satisfied for the funds to be spent.
txin_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                             recipientpubkey, OP_ELSE, blocknum, OP_DROP, OP_HASH160,
                             senderpubkey, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
print("redeem script:", b2x(txin_redeemScript))

# Create P2SH scriptPubKey from redeemScript.
txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
print("p2sh_scriptPubKey", b2x(txin_scriptPubKey))

# Convert the P2SH scriptPubKey to a base58 Bitcoin address
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
p2sh = str(txin_p2sh_address)
print('Pay to:', p2sh)

# AUTOMATE Send funds to p2sh
amount = 1.0*COIN
fund_tx = proxy.sendtoaddress(txin_p2sh_address, amount)

print('Now redeeming.........')

# AUTOMATE getting vout of funding tx
txinfo = proxy.gettransaction(fund_tx)
details = txinfo['details'][0]
vout = details['vout']

# Create the txin structure. scriptSig defaults to being empty.
# The input is the p2sh funding transaction txid, vout is its index
txin = CMutableTxIn(COutPoint(fund_tx, vout))

# Create the txout. Pays out to recipient, so uses recipient's pubkey
# Withdraw full amount minus fee
default_fee = 0.001*COIN
txout = CMutableTxOut(amount - default_fee, recipientpubkey.to_scriptPubKey())

# Create the unsigned raw transaction.
tx = CMutableTransaction([txin], [txout])

# Calculate the signature hash for that transaction. Note how the script we use
# is the redeemScript, not the scriptPubKey. EvalScript() will be evaluating the redeemScript
sighash = SignatureHash(txin_redeemScript, tx, 0, SIGHASH_ALL)

# Now sign it. We have to append the type of signature we want to the end, in
# this case the usual SIGHASH_ALL.
sig = seckey.sign(sighash) + bytes([SIGHASH_ALL])

# Set the scriptSig of our transaction input appropriately.
txin.scriptSig = CScript([ sig, seckey.pub, preimage, OP_TRUE, txin_redeemScript])

print("Redeem tx hex:", b2x(tx.serialize()))

# Verify the signature worked.
VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))

print("Now sending redeem transaction.......")
txid = proxy.sendrawtransaction(tx)
print("Txid of submitted redeem tx: ", b2x(txid))
