# ZBXCAT
A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Contains basic scripts we're still testing in regtest mode on both networks. This may all be refactored as we go.

Bitcoin scripts use the rpc proxy code in python-bitcoinlib, and Zcash script will use python-zcashlib (a Zcash fork of python-bitcoinlib).

## Current status of scripts

The script `btc-p2sh-htlc.py` creates and redeems a p2sh transaction on Bitcoin regtest using a preimage. Locktime scripting still needs work.

To successfully run it, you'll need python3, the dependencies installed, and a bitcoin daemon running in regtest mode.

To install python3 in a virtualenv, run this command from the top level of the directory:
```
virtualenv -p python3 venv
source venv/bin/activate
```

To install dependencies, run:
```
pip install -r requirements.txt
```

To run a bitcoin daemon in regtest mode, with the ability to inspect transactions outside your wallet (useful for testing purposes), use the command
```
bitcoind -regtest -txindex=1 --daemon
```

## Installing python-zcashlib for testing and editing

The Zcash fork of python-bitcoinlib is currently in progress:

`git clone https://github.com/arcalinea/python-bitcoinlib/tree/zcashlib`

You can install this module locally through pip, in editable mode, so that changes you make are applied immediately. To install from local filesystem path:

`pip install --editable (-e) <path-to-zcashlib>`


## Misc

`protocol-pseudocode.py` is guaranteed to not run. It was written as a brainstorm/sketch of a hypothetical xcat protocol using @ebfull's fork of Zcash/Bitcoin that supports createhtlc as an rpc command. Including here in case it's useful in any way.

I used the module [future](http://python-future.org/futurize.html) to make existing python2 code for the rpc interface compatible with python3.
