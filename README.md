# ZBXCAT
A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Contains basic scripts we're still testing in regtest mode on both networks. This may all be refactored as we go.

The ZBXCAT directory contains BitcoinRPC and ZcashRPC, wrappers around the rpc interface that can be imported as Python modules.

The settings.py file in BitcoinRPC and ZcashRPC parse the config files for username/password and set the network ports.

Most functions are named exactly the same as the rpc methods, except for a few additional custom functions that do things like return only the version number.

**EDIT**: The scripts now use the rpc proxy code in python-bitcoinlib, and ZDaemon's functions will be refactored into python-zcashlib (a Zcash fork of python-bitcoinlib)

## Current status of scripts

Run `redeem-preimage-p2sh.py` to test. It creates and redeems a p2sh transaction using a preimage. To successfully run it, you need python3, the dependencies installed, and a bitcoin daemon running in regtest mode.

(Currently only tested on Bitcoin. Need to verify that the Zcash fork of python-bitcoinlib, one of the dependencies, works properly, then figure out the best way to install it.)

`bitcoin-swap.py` contains all the functions that use a proxy to interact with a Bitcoin daemon.

Use python3 to test. To create a virtualenv for python3, run this command from the top level of the directory:
```
virtualenv -p python3 venv
source venv/bin/activate
```

Install dependencies for ZBXCAT: `pip install -r requirements.txt`

## Installing python-zcashlib for testing and editing

The Zcash fork of python-bitcoinlib that is currently in progress:

`git clone https://github.com/arcalinea/python-bitcoinlib/tree/zcashlib`

You can install this module locally through pip, in editable mode, so that changes you make are applied immediately. For install from local filesystem path:

`pip install --editable (-e) <path-to-zcashlib>`


## Misc

`protocol-pseudocode.py` is guaranteed to not run. It was written as a brainstorm/sketch of a hypothetical xcat protocol using @ebfull's fork of Zcash/Bitcoin that supports createhtlc as an rpc command. Including here in case it's useful in any way.

I used the module [future](http://python-future.org/futurize.html) to make existing python2 code for the rpc interface compatible with python3.
