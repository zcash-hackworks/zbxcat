#!/usr/bin/env python3

import sys
import bitcoin
import bitcoin.rpc
from xcat.utils import x2s
from bitcoin.core import b2x, lx, x, COIN, CMutableTxOut
from bitcoin.core import CMutableTxIn, CMutableTransaction
from bitcoin.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF
from bitcoin.core.script import OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG
from bitcoin.core.script import SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP
from bitcoin.core.script import OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, P2SHBitcoinAddress
from bitcoin.wallet import P2PKHBitcoinAddress
import logging

if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

FEE = 0.001 * COIN


class bitcoinProxy():
    def __init__(self, network='regtest', timeout=900):
        if network not in ['testnet', 'mainnet', 'regtest']:
            raise ValueError('Allowed networks are regtest, testnet, mainnet.')
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError('Timeout should be a positive integer.')

        logging.debug("NETWORK in proxy: {0}".format(network))

        self.network = network
        self.timeout = timeout

        bitcoin.SelectParams(self.network)
        self.bitcoind = bitcoin.rpc.Proxy(timeout=self.timeout)

    def validateaddress(self, addr):
        return self.bitcoind.validateaddress(addr)

    def find_secret(self, p2sh, fundtx_input):
        txs = self.bitcoind.call('listtransactions', "*", 20, 0, True)
        for tx in txs:
            raw = self.bitcoind.gettransaction(lx(tx['txid']))['hex']
            decoded = self.bitcoind.decoderawtransaction(raw)
            print("TXINFO", decoded['vin'][0])
            if('txid' in decoded['vin'][0]):
                sendid = decoded['vin'][0]['txid']
                if (sendid == fundtx_input):
                    print("Found funding tx: ", sendid)
                    return self.parse_secret(lx(tx['txid']))
        print("Redeem transaction with secret not found")
        return

    def parse_secret(self, txid):
        raw = self.bitcoind.call('gettransaction', txid, True)['hex']
        decoded = self.bitcoind.call('decoderawtransaction', raw)
        scriptSig = decoded['vin'][0]['scriptSig']
        asm = scriptSig['asm'].split(" ")
        # pubkey = asm[1]
        secret = x2s(asm[2])
        # redeemPubkey = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
        return secret

    def get_keys(self, funder_address, redeemer_address):
        fundpubkey = CBitcoinAddress(funder_address)
        redeempubkey = CBitcoinAddress(redeemer_address)
        # fundpubkey = self.bitcoind.getnewaddress()
        # redeempubkey = self.bitcoind.getnewaddress()
        return fundpubkey, redeempubkey

    def privkey(self, address):
        self.bitcoind.dumpprivkey(address)

    def hashtimelockcontract(self, funder, redeemer, commitment, locktime):
        funderAddr = CBitcoinAddress(funder)
        redeemerAddr = CBitcoinAddress(redeemer)
        if type(commitment) == str:
            commitment = x(commitment)
        # h = sha256(secret)
        blocknum = self.bitcoind.getblockcount()
        print("Current blocknum on Bitcoin: ", blocknum)
        redeemblocknum = blocknum + locktime
        print("Redeemblocknum on Bitcoin: ", redeemblocknum)
        redeemScript = CScript([
            OP_IF, OP_SHA256, commitment, OP_EQUALVERIFY, OP_DUP, OP_HASH160,
            redeemerAddr, OP_ELSE, redeemblocknum, OP_CHECKLOCKTIMEVERIFY,
            OP_DROP, OP_DUP, OP_HASH160, funderAddr, OP_ENDIF, OP_EQUALVERIFY,
            OP_CHECKSIG])
        # print("Redeem script for p2sh contract on Bitcoin blockchain: "
        #        "{0}".format(b2x(redeemScript)))
        txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
        # Convert the P2SH scriptPubKey to a base58 Bitcoin address
        txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(
            txin_scriptPubKey)
        p2sh = str(txin_p2sh_address)
        # Import address at same time you create
        self.bitcoind.importaddress(p2sh, "", False)
        print("p2sh computed", p2sh)
        return {'p2sh': p2sh,
                'redeemblocknum': redeemblocknum,
                'redeemScript': b2x(redeemScript),
                'redeemer': redeemer,
                'funder': funder,
                'locktime': locktime}

    def fund_htlc(self, p2sh, amount):
        send_amount = float(amount) * COIN
        # Import address at same time that you fund it
        self.bitcoind.importaddress(p2sh, "", False)
        fund_txid = self.bitcoind.sendtoaddress(p2sh, send_amount)
        txid = b2x(lx(b2x(fund_txid)))
        return txid

    # Following two functions are about the same
    def check_funds(self, p2sh):
        self.bitcoind.importaddress(p2sh, "", False)
        # Get amount in address
        amount = self.bitcoind.getreceivedbyaddress(p2sh, 0)
        amount = amount / COIN
        return amount

    def get_fund_status(self, p2sh):
        self.bitcoind.importaddress(p2sh, "", False)
        amount = self.bitcoind.getreceivedbyaddress(p2sh, 0)
        amount = amount / COIN
        print("Amount in bitcoin p2sh: ", amount, p2sh)
        if amount > 0:
            return 'funded'
        else:
            return 'empty'

    # TODO: FIX search for p2sh in block
    def search_p2sh(self, block, p2sh):
        print("Fetching block...")
        blockdata = self.bitcoind.getblock(lx(block))
        print("done fetching block")
        txs = blockdata.vtx
        print("txs", txs)
        for tx in txs:
            txhex = b2x(tx.serialize())
            txhex = txhex + '00'
            rawtx = self.bitcoind.call('decoderawtransaction', txhex)
            for vout in rawtx['vout']:
                if 'addresses' in vout['scriptPubKey']:
                    for addr in vout['scriptPubKey']['addresses']:
                        print("Sent to address:", addr)
                        if addr == p2sh:
                            print("Address to p2sh found in transaction!", addr)
        print("Returning from search_p2sh")

    def get_tx_details(self, txid):
        # must convert txid string to bytes x(txid)
        fund_txinfo = self.bitcoind.gettransaction(lx(txid))
        return fund_txinfo['details'][0]

    def redeem_contract(self, contract, secret):
        print("Parsing script for redeem_contract...")
        scriptarray = self.parse_script(contract.redeemScript)
        redeemblocknum = scriptarray[8]
        self.redeemPubKey = P2PKHBitcoinAddress.from_bytes(x(scriptarray[6]))
        # refundPubKey = P2PKHBitcoinAddress.from_bytes(x(scriptarray[13]))
        p2sh = contract.p2sh
        # checking there are funds in the address
        amount = self.check_funds(p2sh)
        if(amount == 0):
            print("address ", p2sh, " not funded")
            quit()
        fundtx = self.find_transaction_to_address(p2sh)
        amount = fundtx['amount'] / COIN
        # print("Found fund_tx: ", fundtx)
        p2sh = P2SHBitcoinAddress(p2sh)
        if fundtx['address'] == p2sh:
            print("Found {0} in p2sh {1}, redeeming...".format(amount, p2sh))

            blockcount = self.bitcoind.getblockcount()
            print("\nCurrent blocknum at time of redeem on Bitcoin:", blockcount)
            if blockcount < int(redeemblocknum):
                return self.redeem(contract, fundtx, secret)
            else:
                print("nLocktime exceeded, refunding")
                return self.refund(contract)
        else:
            print("No contract for this p2sh found in database", p2sh)

    def redeem(self, contract, fundtx, secret):
        print('redeemPubKey', self.redeemPubKey)
        # TODO: Compare with script on blockchain?
        redeemScript = CScript(x(contract.redeemScript))
        txin = CMutableTxIn(fundtx['outpoint'])
        txout = CMutableTxOut(fundtx['amount'] - FEE,
                              self.redeemPubKey.to_scriptPubKey())

        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        sighash = SignatureHash(redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: protect privkey better, separate signing from rawtx creation
        privkey = self.bitcoind.dumpprivkey(self.redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])
        preimage = secret.encode('utf-8')
        txin.scriptSig = CScript([sig, privkey.pub, preimage,
                                  OP_TRUE, redeemScript])

        # print("txin.scriptSig", b2x(txin.scriptSig))
        txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
        print('Raw redeem transaction hex: ', b2x(tx.serialize()))
        VerifyScript(txin.scriptSig, txin_scriptPubKey,
                     tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("Script verified, sending raw transaction...")
        txid = self.bitcoind.sendrawtransaction(tx)
        fund_tx = str(fundtx['outpoint'])
        redeem_tx = b2x(lx(b2x(txid)))
        return {"redeem_tx": redeem_tx, "fund_tx": fund_tx}

    def refund(self, contract):
        fundtx = self.find_transaction_to_address(contract.p2sh)
        print("Fund tx found in refund: ", fundtx)
        refundPubKey = self.find_refundAddr(contract)
        print('refundPubKey: {0}'.format(refundPubKey))

        redeemScript = CScript(x(contract.redeemScript))
        txin = CMutableTxIn(fundtx['outpoint'])
        txout = CMutableTxOut(fundtx['amount'] - FEE,
                              refundPubKey.to_scriptPubKey())

        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # Set nSequence and nLockTime
        txin.nSequence = 0
        tx.nLockTime = contract.redeemblocknum
        sighash = SignatureHash(redeemScript, tx, 0, SIGHASH_ALL)
        privkey = self.bitcoind.dumpprivkey(refundPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])

        # Sign without secret
        txin.scriptSig = CScript([sig, privkey.pub, OP_FALSE, redeemScript])

        # txin.nSequence = 2185
        txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
        print('Raw redeem transaction hex: {0}'.format(b2x(tx.serialize())))
        res = VerifyScript(txin.scriptSig, txin_scriptPubKey,
                           tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("Script verified, sending raw transaction... (NOT)", res)
        txid = self.bitcoind.sendrawtransaction(tx)
        refund_tx = b2x(lx(b2x(txid)))
        fund_tx = str(fundtx['outpoint'])
        return {"refund_tx": refund_tx, "fund_tx": fund_tx}

    def parse_script(self, script_hex):
        redeemScript = self.bitcoind.call('decodescript', script_hex)
        scriptarray = redeemScript['asm'].split(' ')
        return scriptarray

    def find_redeemblocknum(self, contract):
        scriptarray = self.parse_script(contract.redeemScript)
        redeemblocknum = scriptarray[8]
        return int(redeemblocknum)

    def find_redeemAddr(self, contract):
        scriptarray = self.parse_script(contract.redeemScript)
        redeemer = scriptarray[6]
        redeemAddr = P2PKHBitcoinAddress.from_bytes(x(redeemer))
        return redeemAddr

    def find_refundAddr(self, contract):
        scriptarray = self.parse_script(contract.redeemScript)
        funder = scriptarray[13]
        refundAddr = P2PKHBitcoinAddress.from_bytes(x(funder))
        return refundAddr

    def find_transaction_to_address(self, p2sh):
        self.bitcoind.importaddress(p2sh, "", False)
        txs = self.bitcoind.listunspent()
        for tx in txs:
            if tx['address'] == CBitcoinAddress(p2sh):
                logging.debug("Found tx to p2sh: {0}".format(p2sh))
                return tx

    def new_bitcoin_addr(self):
        addr = self.bitcoind.getnewaddress()
        return str(addr)

    def generate(self, num):
        blocks = self.bitcoind.generate(num)
        return blocks
