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
from zcash.core import b2x, x, lx, b2lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
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
    print("Fund address on the Zcash blockchain", txin_p2sh_address)
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
    zcashd.importaddress(p2sh, "", False)
    print("Imported address", p2sh)
    # Get amount in address
    amount = zcashd.getreceivedbyaddress(p2sh, 0)
    print("Amount in address", amount)
    amount = amount/COIN
    return amount

def find_transaction_to_address(p2sh):
    zcashd.importaddress(p2sh, "", False)
    txs = zcashd.listunspent()
    for tx in txs:
        # print("tx addr:", tx['address'])
        # print(type(tx['address']))
        # print(type(p2sh))
        if tx['address'] == CBitcoinAddress(p2sh):
            print(tx)
            return tx


def get_tx_details(txid):
    # This method is problematic I haven't gotten the type conversions right
    print(bytearray.fromhex(txid))
    print(b2x(bytearray.fromhex(txid)))
    fund_txinfo = zcashd.gettransaction(bytearray.fromhex(txid))
    print(fund_txinfo)
    
    return fund_txinfo['details'][0]

def find_secret(p2sh):
    return parse_secret('4c25b5db9f3df48e48306891d8437c69308afa122f92416df1a3ba0d3604882f')
    '''zcashd.importaddress(p2sh, "", False)
    txs = zcashd.listtransactions()
    for tx in txs:
        # print("tx addr:", tx['address'])
        # print(type(tx['address']))
        # print(type(p2sh))
        if (tx['address'] == p2sh ) and (tx['category'] == "send"):
            print(type(tx['txid']))
            print(str.encode(tx['txid']))

            raw = zcashd.getrawtransaction(lx(tx['txid']),True)['hex']
            decoded = zcashd.decoderawtransaction(raw)
            print("deo:", decoded['vin'][0]['scriptSig']['asm'])'''

def parse_secret(txid):
    raw = zcashd.getrawtransaction(lx(txid),True)['hex']
    decoded = zcashd.decoderawtransaction(raw)
    asm = decoded['vin'][0]['scriptSig']['asm'].split(" ")
    print(asm[2])


def redeem(p2sh,side):
    #checking there are funds in the address
    amount = check_funds(p2sh)
    if(amount == 0):
        print("address ", p2sh, " not funded")
        quit()
    fundtx = find_transaction_to_address(p2sh)
    # print("txid:", txid)
    contracts = get_contract()
    trade = get_trade()
    contract = False
    print("p2sh", p2sh)
    for key in contracts:
        if key == p2sh:
            contract = contracts[key]
    if contract:
        print("Redeeming tx in p2sh", p2sh)
        # TODO: Have to get tx info from saved contract p2sh
        redeemblocknum = contract['redeemblocknum']
        zec_redeemScript = CScript(bytearray.fromhex(contract['zec_redeemScript']))

        # txid = trade[side]['fund_tx']
        # details = get_tx_details(txid)
        print(type(fundtx['outpoint']))
        txin = CMutableTxIn(fundtx['outpoint'])
        redeemPubKey = CBitcoinAddress(contract['redeemer'])
        txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
        # TODO: these things like redeemblocknum should really be properties of a tx class...
        # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
        tx.nLockTime = redeemblocknum  # Ariel: This is only needed when redeeming with the timelock
        sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey?
        privkey = zcashd.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        # print(type(contract['secret']))
        # print(contract['secret'])

        txin.scriptSig = CScript([sig, privkey.pub, str.encode(contract['secret']), OP_TRUE, zec_redeemScript])
        print("Redeem tx hex:", b2x(tx.serialize()))

        print("txin.scriptSig", b2x(txin.scriptSig))
        txin_scriptPubKey = fundtx['scriptPubKey']
        # print(type(txin_scriptPubKey))
        print("txin_scriptPubKey", b2x(txin_scriptPubKey))
        print('tx', tx)
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("script verified, sending raw tx")
        txid = zcashd.sendrawtransaction(tx)
        print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
    else:
        print("No contract for this p2sh found in database", p2sh)
