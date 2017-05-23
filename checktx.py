#!/usr/bin/env python3
import sys
import subprocess

subprocess.Popen("source /home/jay/Zcash/python3-xcat/venv/bin/activate", shell=True)

import bitcoin
import bitcoin.rpc
SelectParams('regtest')
bitcoind = bitcoin.rpc.Proxy()

txid = sys.argv[1]
print("Incoming txid:", txid)
tx = bitcoind.gettransaction(txid, 0)
print(tx)
