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
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2PKHBitcoinAddress

from utils import *

import zcash
import zcash.rpc
import pprint, json

# SelectParams('testnet')
SelectParams('regtest')
bitcoind = bitcoin.rpc.Proxy()
FEE = 0.001*COIN

zcashd = zcash.rpc.Proxy()

def import_address(address):
    zcashd.importaddress(address, "", False)

def parse_secret(txid):
    decoded = bitcoind.getrawtransaction(lx(txid), 1)
    # decoded = bitcoind.decoderawtransaction(raw)
    asm = decoded['vin'][0]['scriptSig']['asm'].split(" ")
    print(asm[2])

def get_keys(funder_address, redeemer_address):
    fundpubkey = CBitcoinAddress(funder_address)
    redeempubkey = CBitcoinAddress(redeemer_address)
    # fundpubkey = bitcoind.getnewaddress()
    # redeempubkey = bitcoind.getnewaddress()
    return fundpubkey, redeempubkey

def privkey(address):
    bitcoind.dumpprivkey(address)

def hashtimelockcontract(contract):
    funderAddr = CBitcoinAddress(contract['funder'])
    redeemerAddr = CBitcoinAddress(contract['redeemer'])
    h = contract['hash_of_secret']
    redeemblocknum = contract['redeemblocknum']
    print("REDEEMBLOCKNUM ZCASH", redeemblocknum)
    btc_redeemscript = CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                                 redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                                 funderAddr, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
    print("Redeem script for p2sh contract on Zcash blockchain:", b2x(btc_redeemscript))
    txin_scriptPubKey = btc_redeemscript.to_p2sh_scriptPubKey()
    # Convert the P2SH scriptPubKey to a base58 Bitcoin address
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    p2sh = str(txin_p2sh_address)
    bitcoind.importaddress(p2sh, "", False)
    contract['p2sh'] = p2sh
    contract['redeemscript'] = b2x(btc_redeemscript)
    # Returning all this to be saved locally in p2sh.json
    return contract

def fund_htlc(p2sh, amount):
    send_amount = float(amount) * COIN
    fund_txid = bitcoind.sendtoaddress(p2sh, send_amount)
    txid = b2x(lx(b2x(fund_txid)))
    print("funding btc sell address:", txid)
    return txid

def check_funds(p2sh):
    bitcoind.importaddress(p2sh, "", False)
    # Get amount in address
    amount = bitcoind.getreceivedbyaddress(p2sh, 0)
    amount = amount/COIN
    print("Amount in bitcoin address ", p2sh, ":",amount)
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
    # must convert txid string to bytes x(txid)
    fund_txinfo = bitcoind.gettransaction(lx(txid))
    return fund_txinfo['details'][0]

# redeems funded tx automatically, by scanning for transaction to the p2sh
# i.e., doesn't require buyer telling us fund txid
# returns false if fund tx doesn't exist or is too small
def redeem_with_secret(contract, secret):
    # How to find redeemscript and redeemblocknum from blockchain?
    print("Redeeming contract using secret", contract.__dict__)
    p2sh = contract.p2sh
    minamount = float(contract.amount)
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

        redeemPubKey = find_redeemAddr(contract)
        print('redeemPubKey', redeemPubKey)

        redeemscript = CScript(x(contract.redeemscript))
        txin = CMutableTxIn(fundtx['outpoint'])
        txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        sighash = SignatureHash(redeemscript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey
        privkey = bitcoind.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        print("SECRET", secret)
        preimage = secret.encode('utf-8')
        txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, redeemscript])

        # exit()

        # print("txin.scriptSig", b2x(txin.scriptSig))
        txin_scriptPubKey = redeemscript.to_p2sh_scriptPubKey()
        # print('Redeem txhex', b2x(tx.serialize()))
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("script verified, sending raw tx")
        txid = bitcoind.sendrawtransaction(tx)
        print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
        return  b2x(lx(b2x(txid)))
    else:
        print("No contract for this p2sh found in database", p2sh)



# given a contract return true or false according to whether the relevant fund tx's timelock is still valid
def still_locked(contract):
    p2sh = contract.p2sh
    # Parsing redeemblocknum from the redeemscript of the p2sh
    redeemblocknum = find_redeemblocknum(contract)
    blockcount = bitcoind.getblockcount()
    # print(blockcount, redeemblocknum, blockcount<redeemblocknum)
    if (blockcount < redeemblocknum):
        return True
    else:
        return False

def redeem_after_timelock(contract):
    p2sh = contract.p2sh
    fundtx = find_transaction_to_address(p2sh)
    amount = fundtx['amount'] / COIN

    if (fundtx['address'].__str__() != p2sh):
        print("no fund transaction found to the contract p2sh address ",p2sh)
        quit()
    print("Found fundtx:", fundtx)
    # Parsing redeemblocknum from the redeemscript of the p2sh
    redeemblocknum = find_redeemblocknum(contract)
    blockcount = bitcoind.getblockcount()
    print ("Current block:", blockcount, "Can redeem from block:", redeemblocknum)
    if(still_locked(contract)):
        print("too early for redeeming with timelock try again at block", redeemblocknum, "or later")
        return 0
    
    print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

        
    redeemPubKey = find_refundAddr(contract)
    print('refundPubKey', redeemPubKey)

    redeemscript = CScript(x(contract.redeemscript))
    txin = CMutableTxIn(fundtx['outpoint'])
    txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
    # Create the unsigned raw transaction.
    txin.nSequence = 0
    tx = CMutableTransaction([txin], [txout])
    tx.nLockTime = redeemblocknum
    
    sighash = SignatureHash(redeemscript, tx, 0, SIGHASH_ALL)
    # TODO: figure out how to better protect privkey
    privkey = bitcoind.dumpprivkey(redeemPubKey)
    sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, privkey.pub,  OP_FALSE, redeemscript])

    # exit()

    # print("txin.scriptSig", b2x(txin.scriptSig))
    txin_scriptPubKey = redeemscript.to_p2sh_scriptPubKey()
    # print('Redeem txhex', b2x(tx.serialize()))
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
    print("script verified, sending raw tx")
    txid = bitcoind.sendrawtransaction(tx)
    print("Txid of submitted redeem tx: ", b2x(lx(b2x(txid))))
    return  b2x(lx(b2x(txid)))




# takes hex and returns array of decoded script op codes
def parse_script(script_hex):
    redeemscript = zcashd.decodescript(script_hex)
    scriptarray = redeemscript['asm'].split(' ')
    return scriptarray

def find_redeemblocknum(contract):
    scriptarray = parse_script(contract.redeemscript)
    redeemblocknum = scriptarray[8]
    return int(redeemblocknum)

def find_redeemAddr(contract):
    scriptarray = parse_script(contract.redeemscript)
    redeemer = scriptarray[6]
    redeemAddr = P2PKHBitcoinAddress.from_bytes(x(redeemer))
    return redeemAddr

def find_refundAddr(contract):
    scriptarray = parse_script(contract.redeemscript)
    funder = scriptarray[13]
    refundAddr = P2PKHBitcoinAddress.from_bytes(x(funder))
    return refundAddr

# def find_recipient(contract):
    # initiator = CBitcoinAddress(contract.initiator)
    # fulfiller = CBitcoinAddress(contract.fulfiller)
    # print("Initiator", b2x(initiator))
    # print("Fulfiler", b2x(fulfiller))
    # make this dependent on actual fund tx to p2sh, not contract
    # print("Contract fund_tx", contract.fund_tx)
    # txid = contract.fund_tx
    # raw = bitcoind.gettransaction(lx(txid))['hex']
    # print("Raw tx", raw)
    # # print("Raw", raw)
    # decoded = zcashd.decoderawtransaction(raw + '00')
    # scriptSig = decoded['vin'][0]['scriptSig']
    # print("Decoded", scriptSig)
    # asm = scriptSig['asm'].split(" ")
    # pubkey = asm[1]
    # print('pubkey', pubkey)
    # redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    # print('redeemPubkey', redeemPubkey)

def find_transaction_to_address(p2sh):
    bitcoind.importaddress(p2sh, "", False)
    txs = bitcoind.listunspent()
    for tx in txs:
        # print("tx addr:", )
        # print(type(tx['address']))
        # print(type(p2sh))
        if tx['address'] == CBitcoinAddress(p2sh):
            print("Found tx to p2sh", p2sh)
            return tx

def new_bitcoin_addr():
    addr = bitcoind.getnewaddress()
    print('new btc addr', addr)
    return addr

def generate(num):
    blocks = bitcoind.generate(num)
    return blocks

def find_secret(p2sh,vinid):
    bitcoind.importaddress(p2sh, "", False)
    # is this working?

    txs = bitcoind.listtransactions ()
    print("==========================================LISTTT============", txs)
    print()
    for tx in txs:
        print("tx addr:", tx['address'], "tx id:", tx['txid'])
        raw = bitcoind.gettransaction(lx(tx['txid']))['hex']
        decoded = bitcoind.decoderawtransaction(raw)
        if('txid' in decoded['vin'][0]):
            sendid = decoded['vin'][0]['txid']
            
            if (sendid == vinid ):
                print(type(tx['txid']))
                print(str.encode(tx['txid']))
                return parse_secret(lx(tx['txid']))
    print("Redeem transaction with secret not found")
    return ""

def parse_secret(txid):
    raw = bitcoind.gettransaction(txid)['hex']
    # print("Raw", raw)
    decoded = bitcoind.decoderawtransaction(raw)
    scriptSig = decoded['vin'][0]['scriptSig']
    print("Decoded", scriptSig)
    asm = scriptSig['asm'].split(" ")
    pubkey = asm[1]
    secret = hex2str(asm[2])
    redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    print('redeemPubkey', redeemPubkey)
    print(secret)
    return secret


