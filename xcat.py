#!/usr/bin/env python3

# Based on spend-p2sh-txout.py from python-bitcoinlib.
# Copyright (C) 2017 The Zcash developers

import sys
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

import bitcoin
import bitcoin.rpc
from bitcoin import SelectParams
from bitcoin.core import b2x, lx, b2lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret
import hashlib

# SelectParams('testnet')
SelectParams('regtest')
bitcoind = bitcoin.rpc.Proxy()
FEE = 0.001*COIN

# =========================  BITCOIN ADDRESSES =========================
alicepubkey = CBitcoinAddress('mshp4msfzc73ebg4VzwS6nAXj9t6KqX1wd')
bobpubkey = CBitcoinAddress('myRh2T5Kg7QJfGLeRzriT5zs9aoek5Jbha')
alice_address = input("Enter alice bitcoin address: (type 'enter' for demo)")
bob_address = input("Enter bob bitcoin address: (type 'enter' for demo)")

# bitcoind.getnewaddress() returns CBitcoinAddress
# bobpubkey = bitcoind.getnewaddress()
# alicepubkey = bitcoind.getnewaddress()
# print("alicepubkey", alicepubkey)
# print("bobpubkey", bobpubkey)

print("alice address", alice_address)
print("bob address", bob_address)

# privkey of the bob, used to sign the redeemTx
bob_seckey = bitcoind.dumpprivkey(bob_address)
# privkey of alice, used to refund tx in case of timeout
alice_seckey = bitcoind.dumpprivkey(alice_address)

bobpubkey = CBitcoinAddress(bob_address)
alicepubkey = CBitcoinAddress(alice_address)


print("alicepubkey",alicepubkey )
print("bobpubkey",bobpubkey )


# ========================= HASHLOCK SECRET PREIMAGE =========================
secret = input("Alice: Enter secret to lock funds: (type 'enter' for demo)")
# preimage = secret.encode('UTF-8')
preimage = b'preimage'
h = hashlib.sha256(preimage).digest()

# ========================= LOCKTIME SCRIPT CREATION =========================
lockduration = 10
blocknum = bitcoind.getblockcount()
redeemblocknum = blocknum + lockduration
# Create a htlc redeemScript. Similar to a scriptPubKey the redeemScript must be
# satisfied for the funds to be spent.
btc_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                             alicepubkey, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                             bobpubkey, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
print("Redeem script:", b2x(btc_redeemScript))

# ========================= TX1: CREATE BITCOIN P2SH FROM SCRIPT =========================
txin_scriptPubKey = btc_redeemScript.to_p2sh_scriptPubKey()
# Convert the P2SH scriptPubKey to a base58 Bitcoin address
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
p2sh = str(txin_p2sh_address)
print('Bob -- Assuming Alice has created other tx on Zcash blockchain, send funds to this p2sh address:', p2sh)

## TODO: IMPORT ZCASH XCAT FUNCTIONS


# ========================= FUND BITCOIN P2SH =========================
response = input("Bob -- Type 'enter' to allow zbxcat to fund the Bitcoin p2sh on your behalf:")
send_amount = 1.0*COIN
fund_tx = bitcoind.sendtoaddress(txin_p2sh_address, send_amount)
print('Alice -- Bitcoin fund tx was sent, please wait for confirmation. Txid:', b2x(lx(b2x(fund_tx))))

# ========================= PART 2: BITCOIN P2SH FUNDED, REDEEM OR REFUND =========================
# Check that fund_tx is on the blockchain to the right address, then notify receiver
# Importing address so we can watch it
bitcoind.importaddress(p2sh)
# Get details of funding transaction
fund_txinfo = bitcoind.gettransaction(fund_tx)
fund_details = fund_txinfo['details'] # "fund_details" is an array, for now we can assume it only has one destination address
outputAddress = fund_details[0]['address']
fund_vout = fund_details[0]['vout']
if (outputAddress != p2sh):
    print('Fund tx sent to wrong address! p2sh was {0}, funding tx was sent to {1}'.format(p2sh, outputAddress))
    quit()
# Check amount by inspecting imported address
output_amount = bitcoind.getreceivedbyaddress(outputAddress, 0)
if (output_amount < send_amount):
    print('Fund tx too small! Amount sent was {0}, amount expected was {1}'.format(output_amount, send_amount))
    quit()
print("P2SH {0} successfully funded with {1}".format(p2sh, send_amount))

print('Alice -- the fund tx has been confirmed, now you can redeem your Bitcoin with the secret!')


# ========================= CHECKLOCKIME FOR BITCOIN TX1 =========================
# Mock the timeout period passing for tx1 (comment this out to proceed to redeemtx)
# bitcoind.generate(20)

# ========================= BITCOIN REFUND CONDITION =========================
# AFTER 24 HRS (by blocknum): If locktime for first tx has passed, tx1 is refunded to alice
if(bitcoind.getblockcount() >= redeemblocknum):
    print("Bob -- Alice did not redeem within the timeout period, so refunding your bitcoin....... ")
    txin = CMutableTxIn(COutPoint(fund_tx, fund_vout))
    # The default nSequence of FFFFFFFF won't let you redeem when there's a CHECKTIMELOCKVERIFY
    txin.nSequence = 0
    txout = CMutableTxOut(send_amount - FEE, bobpubkey.to_scriptPubKey())
    # Create the unsigned raw transaction.
    tx = CMutableTransaction([txin], [txout])
    # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
    tx.nLockTime = redeemblocknum
    # Calculate the signature hash for that transaction. Note how the script we use
    # is the redeemScript, not the scriptPubKey. EvalScript() will be evaluating the redeemScript
    sighash = SignatureHash(btc_redeemScript, tx, 0, SIGHASH_ALL)
    sig = bob_seckey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, bob_seckey.pub, OP_FALSE, btc_redeemScript])
    print("Time lock has passed, Bob redeeming his own tx:")
    print("Refund tx hex:", b2x(tx.serialize()))
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
    txid = bitcoind.sendrawtransaction(tx)
    print("Txid of submitted refund tx: ", b2x(lx(b2x(txid))))
    quit()

# ========================= BITCOIN REDEEM CONDITION =========================
# BEFORE 24 HRS (by blocknum): Alice redeems bitcoin tx bob funded
print("Alice -- Redeeming tx.....")
txin = CMutableTxIn(COutPoint(fund_tx, fund_vout))
txout = CMutableTxOut(send_amount - FEE, alicepubkey.to_scriptPubKey())
# Create the unsigned raw transaction.
tx = CMutableTransaction([txin], [txout])
# nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
tx.nLockTime = redeemblocknum
sighash = SignatureHash(btc_redeemScript, tx, 0, SIGHASH_ALL)
sig = alice_seckey.sign(sighash) + bytes([SIGHASH_ALL])
txin.scriptSig = CScript([sig, alice_seckey.pub, preimage, OP_TRUE, btc_redeemScript])
print("Redeem tx hex:", b2x(tx.serialize()))
VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
txid = bitcoind.sendrawtransaction(tx)
print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
