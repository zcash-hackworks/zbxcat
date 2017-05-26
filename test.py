import zcash
import zcash.rpc
from zcash import SelectParams
from zcash.core import b2x, lx, x, b2lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from zcash.core.script import CScript, OP_DUP, OP_IF, OP_ELSE, OP_ENDIF, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_FALSE, OP_DROP, OP_CHECKLOCKTIMEVERIFY, OP_SHA256, OP_TRUE
from zcash.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from zcash.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2PKHBitcoinAddress

addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
print(addr)
print(b2x(addr))

def redeem(p2sh, action):
    trade = get_trade()
    contract = trade[action]
    fundtx = find_transaction_to_address(p2sh)
    p2sh = P2SHBitcoinAddress(p2sh)
    if fundtx['address'] == p2sh:
        print("Redeeming tx in p2sh", p2sh)
        # TODO: Have to get tx info from saved contract p2sh
        redeemblocknum = contract['redeemblocknum']
        zec_redeemScript = contract['redeemScript']

        txid = contract['fund_tx']
        # Replace this with code to find the tx on the blockchain
        # txid = trade[action]['fund_tx']
        details = get_tx_details(txid)
        # print("Txid for fund tx", txid)
        # must be little endian hex
        txin = CMutableTxIn(COutPoint(lx(txid), details['vout']))

        # txin = CMutableTxIn(fundtx['outpoint'])

        redeemPubKey = CBitcoinAddress(contract['initiator'])
        print("redeemPubkey", redeemPubkey)
        amount = trade[action]['amount'] * COIN
        print("amount: {0}, fee: {1}".format(amount, FEE))
        txout = CMutableTxOut(amount - FEE, redeemPubKey.to_scriptPubKey())
        # Create the unsigned raw transaction.
        tx = CMutableTransaction([txin], [txout])
        # nLockTime needs to be at least as large as parameter of CHECKLOCKTIMEVERIFY for script to verify
        # TODO: these things like redeemblocknum should really be properties of a tx class...
        # Need: redeemblocknum, zec_redeemScript, secret (for creator...), txid, redeemer...
        # Is stored as hex, must convert to bytes
        zec_redeemScript = CScript(x(zec_redeemScript))

        tx.nLockTime = redeemblocknum
        sighash = SignatureHash(zec_redeemScript, tx, 0, SIGHASH_ALL)
        # TODO: figure out how to better protect privkey?
        privkey = zcashd.dumpprivkey(redeemPubKey)
        sig = privkey.sign(sighash) + bytes([SIGHASH_ALL])

        # TODO: Figure out where to store secret preimage securely. Parse from scriptsig of redeemtx
        secret = trade['sell']['secret']
        preimage = secret.encode('utf-8')
        print('preimage', preimage)

        # print('zec_redeemScript', zec_redeemScript)
        txin.scriptSig = CScript([sig, privkey.pub, preimage, OP_TRUE, zec_redeemScript])
        # print("Redeem tx hex:", b2x(tx.serialize()))

        # Can only call to_p2sh_scriptPubKey on CScript obj
        txin_scriptPubKey = zec_redeemScript.to_p2sh_scriptPubKey()

        # print("txin.scriptSig", b2x(txin.scriptSig))
        # print("txin_scriptPubKey", b2x(txin_scriptPubKey))
        # print('tx', tx)
        VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, 0, (SCRIPT_VERIFY_P2SH,))
        print("Script verified, sending raw tx...")
        print("Raw tx of prepared redeem tx: ", b2x(tx.serialize()))
        txid = zcashd.sendrawtransaction(tx)
        txhex = b2x(lx(b2x(txid)))
        print("Txid of submitted redeem tx: ", txhex)
        return txhex
    else:
        print("No contract for this p2sh found in database", p2sh)

# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))
