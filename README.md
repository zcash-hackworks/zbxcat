# ZBXCAT

A work-in-progress for Zcash Bitcoin Cross-Chain Atomic Transactions

Bitcoin scripts use python-bitcoinlib, and Zcash scripts use python-zcashlib (a Zcash fork of python-bitcoinlib).

## Setup

To successfully run this code, you'll need python3, the dependencies installed, and a bitcoin and zcash daemon synced on whichever chain you want to trade on.

It's recommended that you install python3 in a virtualenv. Run this command from the top level of the directory:
```
virtualenv -p python3 venv
source venv/bin/activate
```

To install this code, clone the repo and install as a python package.
```
git clone https://github.com/zcash/zbxcat.git
pip install zbxcat
```

To install dependencies, run:
```
pip install -r requirements.txt
```

You'll have to clone the repository to install python-zcashlib.

```
git clone https://github.com/arcalinea/python-zcashlib.git
pip install <path to python-zcashlib>
```

Run Zcash and Bitcoin daemons locally, on whichever network you want to trade on (recommended: testnet, regtest).

Make sure the rpcuser and rpcpassword values are set in your zcash.conf or bitcoin.conf files.

Example `~/.zcash/zcash.conf` file:
```
rpcuser=user
rpcpassword=password
```

## Walking through a new trade

You can try this on regtest on one computer, or on testnet across two computers.

Since this is beta software that is still under active development, we recommend that you do not trade more than you can afford to lose on mainnet.

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


# Testing and Development

You can install modules locally in editable mode through pip, so that you can make changes to the code and they will be applied immediately.

To use pip to install a package in editable mode, use the `-e` flag to pass in the path on your local filesystem:

`pip install -e <path-to-package-repo>`

To install our code as a python package in editable mode, passing in the directory containing `setup.py` should work.

`pip install -e <directory that setup.py for xcat is in>`
