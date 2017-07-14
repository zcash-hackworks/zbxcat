#!/usr/bin/env python3

# Based on spend-p2sh-txout.py from python-bitcoinlib.
# Copyright (C) 2017 The Zcash developers

# small modifications from zXcat.py to be convenient for ETH xcat

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
from zcash.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2PKHBitcoinAddress
import bitcoin
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

def hashtimelockcontract(funder, redeemer, hash_of_secret, lock_increment):
    funderAddr = CBitcoinAddress(funder)
    redeemerAddr = CBitcoinAddress(redeemer)
    blocknum = zcashd.getblockcount()
    print("Current blocknum", blocknum)
    redeemblocknum = blocknum + lock_increment
    print("REDEEMBLOCKNUM ZCASH", redeemblocknum)
    zec_redeemScript = CScript([OP_IF, OP_SHA256, hash_of_secret, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                                 redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                                 funderAddr, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
    print("Redeem script for p2sh contract on Zcash blockchain:", b2x(zec_redeemScript))
    txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
    # Convert the P2SH scriptPubKey to a base58 Bitcoin address
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    p2sh = str(txin_p2sh_address)
    # Returning all this to be saved locally in p2sh.json
    return { 'redeemScript': b2x(zec_redeemScript), 'p2sh': p2sh}



def fund_htlc(p2sh, amount):
    send_amount = float(amount)*COIN
    fund_txid = zcashd.sendtoaddress(p2sh, send_amount)
    txid = b2x(lx(b2x(fund_txid)))
    return txid

def check_funds(p2sh):
    zcashd.importaddress(p2sh, "", False) #Ariel: changed this to true
    print("Imported address", p2sh)
    # Get amount in address
    amount = zcashd.getreceivedbyaddress(p2sh, 0)
    print("Amount in address", amount)
    amount = amount/COIN
    return amount

def get_tx_details(txid):
    fund_txinfo = zcashd.gettransaction(txid)
    return fund_txinfo['details'][0]

def find_transaction_to_address(p2sh):
    zcashd.importaddress(p2sh, "", False)
    txs = zcashd.listunspent()
    for tx in txs:
        if tx['address'] == CBitcoinAddress(p2sh):
            print("Found tx to p2sh", p2sh)
            return tx

# def get_tx_details(txid):
#     # This method is problematic I haven't gotten the type conversions right
#     print(bytearray.fromhex(txid))
#     print(b2x(bytearray.fromhex(txid)))
#     fund_txinfo = zcashd.gettransaction(bytearray.fromhex(txid))
#     print(fund_txinfo)
#
#     return fund_txinfo['details'][0]
def find_secret(p2sh,vinid):
    zcashd.importaddress(p2sh, "", True)
    # is this working?

    txs = zcashd.listtransactions()
    # print("==========================================LISTTT============", txs)
    # print()
    # print('LENNNNNNN:', len(txs))
    # print('LENNNNNNN2:', len(txs))
    for tx in txs:
        # print("tx addr:", tx['address'], "tx id:", tx['txid'])
        # print(type(tx['address']))
        # print(type(p2sh))
        # print('type::',type(tx['txid']))
        raw = zcashd.gettransaction(lx(tx['txid']))['hex']
        decoded = zcashd.decoderawtransaction(raw)
        # print("fdsfdfds", decoded['vin'][0])
        if('txid' in decoded['vin'][0]):
            sendid = decoded['vin'][0]['txid']
            # print("sendid:", sendid)
            
            if (sendid == vinid ):
                # print(type(tx['txid']))
                # print(str.encode(tx['txid']))
                return parse_secret(lx(tx['txid']))
            print("Redeem transaction with secret not found")
            return ""


def parse_secret(txid):
    raw = zcashd.gettransaction(txid)['hex']
    # print("Raw", raw)
    decoded = zcashd.decoderawtransaction(raw)
    scriptSig = decoded['vin'][0]['scriptSig']
    print("Decoded", scriptSig)
    asm = scriptSig['asm'].split(" ")
    pubkey = asm[1]
    secret = hex2str(asm[2])
    redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    print('redeemPubkey', redeemPubkey)
    print(secret)
    return secret

# redeems automatically after buyer has funded tx, by scanning for transaction to the p2sh
# i.e., doesn't require buyer telling us fund txid

def auto_redeem(p2sh, secret):
# How to find redeemScript and redeemblocknum from blockchain?
    print("Contract in auto redeem", contract.__dict__)
    p2sh = contract.p2sh
    #checking there are funds in the address
    amount = check_funds(p2sh)
    if(amount == 0):
        print("address ", p2sh, " not funded")
        quit()
    fundtx = find_transaction_to_address(p2sh)
    amount = fundtx['amount'] / COIN
    p2sh = P2SHBitcoinAddress(p2sh)
    if fundtx['address'] == p2sh:
        print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

        # Parsing redeemblocknum from the redeemscript of the p2sh
        redeemblocknum = find_redeemblocknum(contract)
        blockcount = zcashd.getblockcount()
        print("\nCurrent blocknum at time of redeem on Zcash chain:", blockcount)
        if blockcount < redeemblocknum:
            redeemPubKey = find_redeemAddr(contract)
            print('redeemPubKey', redeemPubKey)
        else:
            print("nLocktime exceeded, refunding")
            redeemPubKey = find_refundAddr(contract)
            print('refundPubKey', redeemPubKey)
        # redeemPubKey = CBitcoinAddress.from_scriptPubKey(redeemPubKey)
        # exit()

        zec_redeemScript = CScript(x(contract.redeemScript))
        txin = CMutableTxIn(fundtx['outpoint'])
        txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
        # TODO: these things like redeemblocknum should really be properties of a tx class...
        # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
        if blockcount >= redeemblocknum:
            print("\nLocktime exceeded")
            tx.nLockTime = redeemblocknum  
        sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey
        privkey = zcashd.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        print("SECRET", secret)
        preimage = secret.encode('utf-8')
        txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, zec_redeemScript])

        # exit()

        # print("txin.scriptSig", b2x(txin.scriptSig))
        txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
        # print('Redeem txhex', b2x(tx.serialize()))
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("script verified, sending raw tx")
        txid = bitcoind.sendrawtransaction(tx)
        print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
        return  b2x(lx(b2x(txid)))
    else:
        print("No contract for this p2sh found in database", p2sh)

def parse_script(script_hex):
    redeemScript = zcashd.decodescript(script_hex)
    scriptarray = redeemScript['asm'].split(' ')
    return scriptarray

def find_redeemblocknum(redeemscript):
    scriptarray = parse_script(redeemScript)
    redeemblocknum = scriptarray[8]
    return int(redeemblocknum)

def find_redeemAddr(redeemscript):
    scriptarray = parse_script(redeemScript)
    redeemer = scriptarray[6]
    redeemAddr = P2PKHBitcoinAddress.from_bytes(x(redeemer))
    return redeemAddr

def find_refundAddr(redeemscript):
    scriptarray = parse_script(redeemScript)
    funder = scriptarray[13]
    refundAddr = P2PKHBitcoinAddress.from_bytes(x(funder))  
    return refundAddr

def find_recipient(contract):
    # make this dependent on actual fund tx to p2sh, not contract
    txid = contract.fund_tx
    raw = zcashd.gettransaction(lx(txid), True)['hex']
    # print("Raw", raw)
    decoded = zcashd.decoderawtransaction(raw)
    scriptSig = decoded['vin'][0]['scriptSig']
    print("Decoded", scriptSig)
    asm = scriptSig['asm'].split(" ")
    pubkey = asm[1]
    initiator = CBitcoinAddress(contract.initiator)
    fulfiller = CBitcoinAddress(contract.fulfiller)
    print("Initiator", b2x(initiator))
    print("Fulfiler", b2x(fulfiller))
    print('pubkey', pubkey)
    redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    print('redeemPubkey', redeemPubkey)

# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))

def new_zcash_addr():
    addr = zcashd.getnewaddress()
    print('new ZEC addr', addr)
    return addr

def generate(num):
    blocks = zcashd.generate(num)
    return blocks




# redeems funded tx automatically, by scanning for transaction to the p2sh
# i.e., doesn't require buyer telling us fund txid
# returns false if fund tx doesn't exist or is too small
# minamout - the minimal amount your're expecting
# assumes your Zcash client has the private key of the legit redeemer
def redeem_with_secret(redeemscript,secret,p2sh,minamount):
    # How to find redeemScript and redeemblocknum from blockchain?
    # print("Redeeming contract using secret", contract.__dict__)
    #checking there are funds in the address
    amount = check_funds(p2sh)
    if(amount < minamount):
        print("address ", p2sh, " not sufficiently funded")
        return false
    fundtx = find_transaction_to_address(p2sh)
    amount = fundtx['amount'] / COIN
    p2sh = P2SHBitcoinAddress(p2sh)
    if fundtx['address'] == p2sh:
        print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

        redeemPubKey = find_redeemAddr(redeemscript)
        print('redeemPubKey', redeemPubKey)

        redeemScriptObject = CScript(x(redeemScript))
        txin = CMutableTxIn(fundtx['outpoint'])
        txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        sighash = SignatureHash(redeemScriptObject, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey
        privkey = zcashd.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        print("SECRET", secret)
        preimage = secret.encode('utf-8')
        txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, redeemScriptObject])

        # exit()

        # print("txin.scriptSig", b2x(txin.scriptSig))
        txin_scriptPubKey = redeemScriptObject.to_p2sh_scriptPubKey()
        # print('Redeem txhex', b2x(tx.serialize()))
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("script verified, sending raw tx")
        txid = zcashd.sendrawtransaction(tx)
        print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
        return  b2x(lx(b2x(txid)))
    else:
        print("No contract for this p2sh found in database", p2sh)



# given a contract return true or false according to whether the relevant fund tx's timelock is still valid
def still_locked(contract):
    p2sh = contract.p2sh
    # Parsing redeemblocknum from the redeemscript of the p2sh
    redeemblocknum = find_redeemblocknum(contract)
    blockcount = zcashd.getblockcount()
    return (int(blockcount) < int(redeemblocknum))

def redeem_after_timelock(redeemscript,redeempubkey,p2sh,fund_txid):
    amount = fundtx['amount'] / COIN

    if (fundtx['address'].__str__() != p2sh):
        print("no fund transaction found to the contract p2sh address ",p2sh)
        quit()
    # print("Found fundtx:", fundtx)
    # Parsing redeemblocknum from the redeemscript of the p2sh
    redeemblocknum = find_redeemblocknum(redeemscript)
    blockcount = zcashd.getblockcount()
    print ("Current block:", blockcount, "Can redeem from block:", redeemblocknum)
    if(still_locked(contract)):
        print("too early for redeeming with timelock try again at block", redeemblocknum, "or later")
        return
    
    print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

        
    redeemPubKey = find_refundAddr(redeemscript)
    print('refundPubKey', redeemPubKey)

    redeemScriptObject = CScript(x(contract.redeemScript))
    txin = CMutableTxIn(fundtx['outpoint'])
    txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
    # Create the unsigned raw transaction.
    txin.nSequence = 0
    tx = CMutableTransaction([txin], [txout])
    tx.nLockTime = redeemblocknum
    
    sighash = SignatureHash(redeemScriptObject, tx, 0, SIGHASH_ALL)
    # TODO: figure out how to better protect privkey
    privkey = zcashd.dumpprivkey(redeemPubKey)
    sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, privkey.pub,  OP_FALSE, redeemScriptObject])

    # exit()

    # print("txin.scriptSig", b2x(txin.scriptSig))
    txin_scriptPubKey = redeemScriptObject.to_p2sh_scriptPubKey()
    # print('Redeem txhex', b2x(tx.serialize()))
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
    print("script verified, sending raw tx")
    txid = zcashd.sendrawtransaction(tx)
    print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
    return  b2x(lx(b2x(txid)))
