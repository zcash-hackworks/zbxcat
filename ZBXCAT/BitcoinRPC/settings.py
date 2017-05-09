import os, re

TIMEOUT = 100
#Default fee to use on network for txs.
DEFAULT_FEE = 0.01
# Default network is testnet
NETWORK = 'TESTNET'
def network_url(network):
	if network == 'TESTNET':
	 	return "http://localhost:18332"
	if network == 'REGTEST':
		return "http://localhost:18332"
	if network == 'MAINNET':
	 	return "http://localhost:8332"

bitcoinconf = os.path.expanduser('~/.bitcoin/bitcoin.conf')
def read_config(filename):
    f = open(filename)
    for line in f:
        if re.match('rpcuser', line):
            user = line.strip('\n').split('=')[1]
        if re.match('rpcpassword', line):
            password = line.strip('\n').split('=')[1]
    return (user, password)
config = read_config(bitcoinconf)
# from bitcoin.conf
RPCUSER = config[0]
RPCPASSWORD = config[1]
