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

from xcat.utils import *
from xcat.zcashRPC import parse_script

SelectParams('testnet')
# SelectParams('regtest')
# TODO: Accurately read user and pw info
bitcoind = bitcoin.rpc.Proxy(timeout=900)
FEE = 0.001*COIN

def validateaddress(addr):
    return bitcoind.validateaddress(addr)

def find_secret(p2sh, fundtx_input):
    txs = bitcoind.call('listtransactions', "*", 20, 0, True)
    for tx in txs:
        raw = bitcoind.gettransaction(lx(tx['txid']))['hex']
        decoded = bitcoind.decoderawtransaction(raw)
        print("TXINFO", decoded['vin'][0])
        if('txid' in decoded['vin'][0]):
            sendid = decoded['vin'][0]['txid']
            if (sendid == fundtx_input ):
                print("Found funding tx: ", sendid)
                return parse_secret(lx(tx['txid']))
    print("Redeem transaction with secret not found")
    return

def parse_secret(txid):
    raw = zcashd.gettransaction(txid, True)['hex']
    decoded = zcashd.call('decoderawtransaction', raw)
    scriptSig = decoded['vin'][0]['scriptSig']
    asm = scriptSig['asm'].split(" ")
    pubkey = asm[1]
    secret = x2s(asm[2])
    redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    return secret

def get_keys(funder_address, redeemer_address):
    fundpubkey = CBitcoinAddress(funder_address)
    redeempubkey = CBitcoinAddress(redeemer_address)
    # fundpubkey = bitcoind.getnewaddress()
    # redeempubkey = bitcoind.getnewaddress()
    return fundpubkey, redeempubkey

def privkey(address):
    bitcoind.dumpprivkey(address)

def hashtimelockcontract(funder, redeemer, commitment, locktime):
    funderAddr = CBitcoinAddress(funder)
    redeemerAddr = CBitcoinAddress(redeemer)
    if type(commitment) == str:
        commitment = x(commitment)
    # h = sha256(secret)
    blocknum = bitcoind.getblockcount()
    print("Current blocknum on Bitcoin: ", blocknum)
    redeemblocknum = blocknum + locktime
    print("Redeemblocknum on Bitcoin: ", redeemblocknum)
    redeemScript = CScript([OP_IF, OP_SHA256, commitment, OP_EQUALVERIFY,OP_DUP, OP_HASH160,
                                 redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY, OP_DROP, OP_DUP, OP_HASH160,
                                 funderAddr, OP_ENDIF,OP_EQUALVERIFY, OP_CHECKSIG])
    # print("Redeem script for p2sh contract on Bitcoin blockchain: {0}".format(b2x(redeemScript)))
    txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
    # Convert the P2SH scriptPubKey to a base58 Bitcoin address
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    p2sh = str(txin_p2sh_address)
    # Import address at same time you create
    bitcoind.importaddress(p2sh, "", False)
    print("p2sh computed", p2sh)
    return {'p2sh': p2sh, 'redeemblocknum': redeemblocknum, 'redeemScript': b2x(redeemScript), 'redeemer': redeemer, 'funder': funder, 'locktime': locktime}

def fund_htlc(p2sh, amount):
    send_amount = float(amount) * COIN
    # Import address at same time that you fund it
    bitcoind.importaddress(p2sh, "", False)
    fund_txid = bitcoind.sendtoaddress(p2sh, send_amount)
    txid = b2x(lx(b2x(fund_txid)))
    return txid

# Following two functions are about the same
def check_funds(p2sh):
    bitcoind.importaddress(p2sh, "", False)
    # Get amount in address
    amount = bitcoind.getreceivedbyaddress(p2sh, 0)
    amount = amount/COIN
    return amount

def get_fund_status(p2sh):
    bitcoind.importaddress(p2sh, "", False)
    amount = bitcoind.getreceivedbyaddress(p2sh, 0)
    amount = amount/COIN
    print("Amount in bitcoin p2sh: ", amount, p2sh)
    if amount > 0:
        return 'funded'
    else:
        return 'empty'

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

def redeem_contract(contract, secret):
    print("Parsing script for redeem_contract...")
    scriptarray = parse_script(contract.redeemScript)
    redeemblocknum = scriptarray[8]
    redeemPubKey = P2PKHBitcoinAddress.from_bytes(x(scriptarray[6]))
    refundPubKey = P2PKHBitcoinAddress.from_bytes(x(scriptarray[13]))
    p2sh = contract.p2sh
    #checking there are funds in the address
    amount = check_funds(p2sh)
    if(amount == 0):
        print("address ", p2sh, " not funded")
        quit()
    fundtx = find_transaction_to_address(p2sh)
    amount = fundtx['amount'] / COIN
    # print("Found fund_tx: ", fundtx)
    p2sh = P2SHBitcoinAddress(p2sh)
    if fundtx['address'] == p2sh:
        print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

        blockcount = bitcoind.getblockcount()
        print("\nCurrent blocknum at time of redeem on Zcash:", blockcount)
        if blockcount < int(redeemblocknum):
            print('redeemPubKey', redeemPubKey)
            zec_redeemScript = CScript(x(contract.redeemScript))
            txin = CMutableTxIn(fundtx['outpoint'])
            txout = CMutableTxOut(fundtx['amount'] - FEE, redeemPubKey.to_scriptPubKey())
            # Create the unsigned raw transaction.
            tx = CMutableTransaction([txin], [txout])
            sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
            # TODO: protect privkey better, separate signing from rawtx creation
            privkey = bitcoind.dumpprivkey(redeemPubKey)
            sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
            preimage = secret.encode('utf-8')
            txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, zec_redeemScript])

            # print("txin.scriptSig", b2x(txin.scriptSig))
            txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()
            print('Raw redeem transaction hex: ', b2x(tx.serialize()))
            VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
            print("Script verified, sending raw transaction...")
            txid = bitcoind.sendrawtransaction(tx)
            fund_tx = str(fundtx['outpoint'])
            redeem_tx =  b2x(lx(b2x(txid)))
            return  {"redeem_tx": redeem_tx, "fund_tx": fund_tx}
        else:
            print("nLocktime exceeded, refunding")
            print('refundPubKey', refundPubKey)
            txid = bitcoind.sendtoaddress(refundPubKey, fundtx['amount'] - FEE)
            fund_tx = str(fundtx['outpoint'])
            refund_tx =  b2x(lx(b2x(txid)))
            return  {"refund_tx": refund_tx, "fund_tx": fund_tx}
    else:
        print("No contract for this p2sh found in database", p2sh)

def find_redeemblocknum(contract):
    scriptarray = parse_script(contract.redeemScript)
    redeemblocknum = scriptarray[8]
    return int(redeemblocknum)

def find_redeemAddr(contract):
    scriptarray = parse_script(contract.redeemScript)
    redeemer = scriptarray[6]
    redeemAddr = P2PKHBitcoinAddress.from_bytes(x(redeemer))
    return redeemAddr

def find_refundAddr(contract):
    scriptarray = parse_script(contract.redeemScript)
    funder = scriptarray[13]
    refundAddr = P2PKHBitcoinAddress.from_bytes(x(funder))
    return refundAddr

def find_transaction_to_address(p2sh):
    bitcoind.importaddress(p2sh, "", False)
    txs = bitcoind.listunspent()
    for tx in txs:
        if tx['address'] == CBitcoinAddress(p2sh):
            print("Found tx to p2sh", p2sh)
            return tx

def new_bitcoin_addr():
    addr = bitcoind.getnewaddress()
    return str(addr)

def generate(num):
    blocks = bitcoind.generate(num)
    return blocks
