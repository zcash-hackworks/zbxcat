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
import hashlib

# SelectParams('testnet')
SelectParams('regtest')
zcashd = zcash.rpc.Proxy()
FEE = 0.001*COIN

# =========================  ZCASH ADDRESSES =========================
alice_address = input("Enter alice zcash address: (type 'enter' for demo)")
bob_address = input("Enter bob zcash address: (type 'enter' for demo)")
# These mock addresses come from regtest on the server
# alicepubkey = CBitcoinAddress('tmFUm31B9wzHWJ9jGe9L9Qb549zfC7zFsEK')
# bobpubkey = CBitcoinAddress('tmFm8R6b22485uDYm6dryC4f8R6oXUTUe5i')
# zcashd.getnewaddress() returns CBitcoinAddress
bobpubkey = zcashd.getnewaddress()
alicepubkey = zcashd.getnewaddress()
print("alicepubkey", alicepubkey)
print("bobpubkey", bobpubkey)
# privkey of the bob, used to sign the redeemTx
bob_seckey = zcashd.dumpprivkey(bobpubkey)
# privkey of alice, used to refund tx in case of timeout
alice_seckey = zcashd.dumpprivkey(alicepubkey)
print("bob_seckey", bob_seckey)

def get_keys(funder_address, redeemer_address):
    # fundpubkey = CBitcoinAddress(funder_address)
    # redeempubkey = CBitcoinAddress(redeemer_address)
    fundpubkey = zcashd.getnewaddress()
    redeempubkey = zcashd.getnewaddress()
    return fundpubkey, redeempubkey

# ======= secret from Alice, other file ====
preimage = b'preimage'
h = hashlib.sha256(preimage).digest()

# ========================= LOCKTIME SCRIPT CREATION =========================
lockduration = 20 # Must be more than first tx
blocknum = zcashd.getblockcount()
redeemblocknum = blocknum + lockduration
zec_redeemScript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                             bobpubkey, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                             alicepubkey, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
print("TX2 Redeem script on Zcash blockchain:", b2x(zec_redeemScript))

# ========================= TX1: CREATE BITCOIN P2SH FROM SCRIPT =========================
txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
# Convert the P2SH scriptPubKey to a base58 Bitcoin address
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
p2sh = str(txin_p2sh_address)
print('Alice -- send funds to this p2sh address to initiate atomic swap:', p2sh)

response = input("Alice -- Type 'enter' to allow zbxcat to fund the Zcash p2sh on your behalf:")
send_amount = 10.0*COIN
fund_tx = zcashd.sendtoaddress(txin_p2sh_address, send_amount)
print('Bob -- Alice send fund tx to the Zcash p2sh. Please wait for confirmation. Txid:', b2x(lx(b2x(fund_tx))))

# ========================= CONFIRM ZCASH FUNDING TX TO P2SH =========================
zcashd.importaddress(p2sh)

fund_txinfo = zcashd.gettransaction(fund_tx)
fund_details = fund_txinfo['details'] # "fund_details" is an array, for now we can assume it only has one destination address
outputAddress = fund_details[0]['address']
fund_vout = fund_details[0]['vout']
if (outputAddress != p2sh):
    print('Fund tx sent to wrong address! p2sh was {0}, funding tx was sent to {1}'.format(p2sh, outputAddress))
    quit()
# Get amount in address
output_amount = zcashd.getreceivedbyaddress(outputAddress, 0)
if (output_amount < send_amount):
    print('Fund tx too small! Amount sent was {0}, amount expected was {1}'.format(output_amount, send_amount))
    quit()

print('Bob -- Alice Zcash funding tx confirmed, now send funds to the Bitcoin p2sh: (other file)')

# ========================= PART 2: ZCASH P2SH FUNDED, REDEEM OR REFUND =========================

# ================= AFTER 48 HRS: ALICE REFUNDS AFTER BOB TIMES OUT =========================
# Mock passage of time -- comment out to test normal redeem condition
# zcashd.generate(25)

if(zcashd.getblockcount() >= redeemblocknum):
    print("Alice -- Bob did not redeem the Zcash you put in escrow within the timeout period, so refunding you..... ")
    txin = CMutableTxIn(COutPoint(fund_tx, fund_vout))
    # The default nSequence of FFFFFFFF won't let you redeem when there's a CHECKTIMELOCKVERIFY
    txin.nSequence = 0
    txout = CMutableTxOut(send_amount - FEE, alicepubkey.to_scriptPubKey())
    # Create the unsigned raw transaction.
    tx = CMutableTransaction([txin], [txout])
    # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
    tx.nLockTime = redeemblocknum
    # Calculate the signature hash for that transaction. Note how the script we use
    # is the redeemScript, not the scriptPubKey. EvalScript() will be evaluating the redeemScript
    sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
    sig = alice_seckey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, alice_seckey.pub, OP_FALSE, zec_redeemScript])
    print("Time lock has passed, Alice redeeming her own tx:")
    print("Refund tx hex:", b2x(tx.serialize()))
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
    txid = zcashd.sendrawtransaction(tx)
    print("Txid of submitted refund tx: ", b2x(lx(b2x(txid))))
    quit()

# ================= BEFORE 48 HRS: BOB REDEEMS WITH ALICE'S REVEALED SECRET =========================
print("Bob -- Redeeming tx.....")
txin = CMutableTxIn(COutPoint(fund_tx, fund_vout))
txout = CMutableTxOut(send_amount - FEE, bobpubkey.to_scriptPubKey())
# Create the unsigned raw transaction.
tx = CMutableTransaction([txin], [txout])
# nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
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
