# Workflow for a new trade

Install our code as a python package in editable mode. Installing relative to the protocol directory should work.
`pip install -e protocol/`

Seller:
To initiate a new trade, seller creates a trade and names it.
`xcat newtrade testtrade`

After creating, they are prompted to export it as hex, to transfer info to the buyer.
`xcat exporttrade testtrade`
Copy the resulting hex string and send it to the buyer.

Buyer:
To examine trade, buyer imports it.
`xcat importttrade <hexstring> testtrade`

If it looks ok, inform seller to proceed.

Seller:
Funds sell p2sh. They can use the checktrade command to automatically take the next step in this trade.
`xcat checktrade testtrade`

Buyer:
Funds by p2sh. Also uses checktrade command locally.
`xcat checktrade testtrade`

Seller:
Redeems buyer p2sh.
`xcat checktrade testtrade`

**At this stage, we need to manually export the trade again, because we haven't added the `walletnotify` functionality which will let the buyer determine what the seller's redeem tx was.**

So seller exports trade again and sends to seller, so they have the seller's redeem_tx. (this is a temporary measure)
`xcat exportrade testtrade`

Buyer:
Imports exported trade.
`xcat importtrade <hexstring> testtrade`

Redeems seller p2sh.
`xcat checktrade testtrade`

Tx is done! Buyer or seller can check the trade again, but the status will indicate that it is complete.

# ZBXCAT

A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Contains basic scripts we're still testing in regtest mode on both networks. This may all be refactored as we go.

Bitcoin scripts use the rpc proxy code in python-bitcoinlib, and Zcash script will use python-zcashlib (a Zcash fork of python-bitcoinlib).

## Setup

To successfully run this, you'll need python3, the dependencies installed, and a bitcoin daemon running in regtest mode.

To install python3 in a virtualenv, run this command from the top level of the directory:
```
virtualenv -p python3 venv
source venv/bin/activate
```

To install dependencies, run:
```
pip install -r requirements.txt
```

To install python-zcashlib for testing and editing, clone the repository to your local filesystem. It is currently on a branch of python-bitcoinlib maintained by @arcalinea.

```
git clone https://github.com/arcalinea/python-bitcoinlib.git
cd python-bitcoinlib
git checkout zcashlib
```

Then, install the module locally in editable mode through pip, so that you can make changes to the code of python-zcashlib and they will be applied immediately. It is necessary to install python-zcashlib this way for now because the fork of the library likely contains many bugs, which need to be fixed before `zec-p2sh-htlc.py` will work properly.

To install python-zcashlib from your local filesystem path in editable mode:

`pip install --editable (-e) <path-to-zcashlib-fork-of-python-bitcoinlib>`

## Run Zcash and Bitcoin daemons locally

To test, run a Zcash daemon and bitcoin daemon in regtest mode. You may have to change the port one of them runs on, for example with the flag `-port=18445`.

To run a bitcoin daemon in regtest mode, with the ability to inspect transactions outside your wallet (useful for testing purposes), use the command
```
bitcoind -regtest -txindex=1 -daemon -port=18445
```

Be sure to run a Zcash daemon in regtest mode.
```
zcashd -regtest -txindex=1 --daemon
```

## Misc

I used the module [future](http://python-future.org/futurize.html) to make existing python2 code for the rpc interface compatible with python3.
