# ZBXCAT
A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Contains basic scripts we're still testing in regtest mode on both networks. This may all be refactored as we go.

Bitcoin scripts use the rpc proxy code in python-bitcoinlib, and Zcash script will use python-zcashlib (a Zcash fork of python-bitcoinlib).

## BTC p2sh HTLC script

The script `btc-p2sh-htlc.py` creates and redeems a p2sh transaction on Bitcoin regtest using a preimage. TODO: Locktime scripting still needs work.

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

## ZEC p2sh HTLC script

The script `zec-p2sh-htlc.py` is the same as the BTC script, but uses python-zcashlib, which is still a work in progress.

To install python-zcashlib for testing and editing, clone the repository to your local filesystem. It is currently on a branch of python-bitcoinlib maintained by @arcalinea.

```
git clone https://github.com/arcalinea/python-bitcoinlib.git
cd python-bitcoinlib
git checkout zcashlib
```

Then, install the module locally in editable mode through pip, so that you can make changes to the code of python-zcashlib and they will be applied immediately. It is necessary to install python-zcashlib this way for now because the fork of the library likely contains many bugs, which need to be fixed before `zec-p2sh-htlc.py` will work properly.

To install python-zcashlib from your local filesystem path in editable mode:

`pip install --editable (-e) <path-to-zcashlib-fork-of-python-bitcoinlib>`

Be sure to run a Zcash daemon in regtest mode.
```
zcashd -regtest -txindex=1 --daemon
```

## Misc

`protocol-pseudocode.py` is guaranteed to not run. It was written as a brainstorm/sketch of a hypothetical xcat protocol using @ebfull's fork of Zcash/Bitcoin that supports createhtlc as an rpc command. Including here in case it's useful in any way.

I used the module [future](http://python-future.org/futurize.html) to make existing python2 code for the rpc interface compatible with python3.
