# ZBXCAT

A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Bitcoin scripts use python-bitcoinlib, and Zcash scripts use python-zcashlib (a Zcash fork of python-bitcoinlib).

## Setup

To successfully run this, you'll need python3, the dependencies installed, and a bitcoin and zcash daemon synced on whichever chain you want to trade on.

It's recommended that you install python3 in a virtualenv. Run this command from the top level of the directory:
```
virtualenv -p python3 venv
source venv/bin/activate
```

To install dependencies, run:
```
pip install -r requirements.txt
```

To install python-zcashlib for testing and editing, clone the repository to your local filesystem.

```
git clone https://github.com/arcalinea/python-zcashlib.git
```

# Testing

Install modules locally in editable mode through pip, so that you can make changes to the code and they will be applied immediately.

To use pip to install a package in editable mode, use the `-e` flag to pass in the path on your local filesystem:

`pip install -e <path-to-package-repo>`

## Run Zcash and Bitcoin daemons locally

To test, run a Zcash daemon and bitcoin daemon in regtest mode.

To run a bitcoin daemon in regtest mode, with the ability to inspect transactions outside your wallet (useful for testing purposes), use the command
```
bitcoind -regtest -txindex=1 -daemon
```

Be sure to run a Zcash daemon in regtest mode as well.
```
zcashd -regtest -txindex=1 --daemon
```


## Workflow for a new trade

Install our code as a python package in editable mode. Installing relative to the directory containing `setup.py` should work.

`pip install -e <directory that setup.py for xcat is in>`

### Seller:

To initiate a new trade, seller creates a trade and names it.

`xcat newtrade testtrade`

After creating, they are prompted to export it as hex, to transfer info to the buyer.

`xcat exporttrade testtrade`

Copy the resulting hex string and send it to the buyer.

### Buyer:

To examine trade, buyer imports it.

`xcat importttrade <hexstring> testtrade`

If it looks ok, inform seller to proceed.

### Seller:

Funds sell p2sh. They can use the checktrade command to automatically take the next step in this trade.

`xcat checktrade testtrade`

### Buyer:

Funds buy p2sh, also by using checktrade command to automatically proceed.

`xcat checktrade testtrade`

### Seller:

Redeems buyer p2sh.

`xcat checktrade testtrade`

### Buyer:

Redeems seller p2sh. The secret they need to redeem will be automatically parsed from the seller's redeemtx on the blockchain.

`xcat checktrade testtrade`

Trade is done! Buyer or seller can check the status again, but it will indicate that it is complete.
