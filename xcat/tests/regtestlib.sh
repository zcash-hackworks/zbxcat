#!/bin/bash

export BITCOINDIR=$(pwd)/bitcoindir
ZCASHDIR=$(pwd)/zcashdir

echo $BITCOINDIR
echo $ZCASHDIR

fail() {
	echo $@
	exit 1
}

bitcoincli() {
	if [ "${BITCOINSRC}" != "" ]; then
			$BITCOINSRC/bitcoin-cli -datadir="$BITCOINDIR" -regtest -rpcserialversion=0 -rpcuser=user -rpcpassword=password $@
		else
			bitcoin-cli -datadir="$BITCOINDIR" -regtest -rpcserialversion=0 -rpcuser=user -rpcpassword=password $@
	fi
}

bdaemon() {
	if [ "${BITCOINSRC}" != "" ]; then
			echo "Bitcoin source directory specified"
			$BITCOINSRC/bitcoind -datadir="$BITCOINDIR" -rpcserialversion=0 -regtest -rpcuser=user -rpcpassword=password  &
		else
			bitcoind -datadir="$BITCOINDIR" -rpcserialversion=0 -regtest -rpcuser=user -rpcpassword=password  &
	fi
}

start_bitcoin() {
	echo "Starting bitcoin..."
	mkdir "$BITCOINDIR"
	bdaemon
	echo $! > bitcoin_pid
	sleep 5
	for i in `seq 101`
	do
		printf "bitcoin block generate %d\r" $i
		bitcoincli generate 1 > /dev/null
	done
	echo ""
}

stop_bitcoin() {
	if [ -e bitcoin_pid ]; then kill $(cat bitcoin_pid); fi
	rm -f bitcoin_pid
	rm -rf "$BITCOINDIR"
}

zcashcli() {
	if [ "${ZCASHSRC}" != "" ]; then
			$ZCASHSRC/zcash-cli -datadir="$ZCASHDIR" -regtest $@
		else
			zcash-cli -datadir="$ZCASHDIR" -regtest $@
	fi
}

zdaemon(){
	if [ "${ZCASHSRC}" != "" ]; then
			$ZCASHSRC/zcashd -datadir="$ZCASHDIR" -regtest -listen=0 &
		else
			zcashd -datadir="$ZCASHDIR" -regtest -listen=0 &
	fi
}

start_zcash() {
	echo "Starting zcash..."
	mkdir "$ZCASHDIR"
	echo "rpcuser=user" > "$ZCASHDIR/zcash.conf"
	echo "rpcpassword=password" >> "$ZCASHDIR/zcash.conf"
	zdaemon
	echo $! > zcash_pid
	sleep 5
	for i in `seq 101`
	do
		printf "zcash block generate %d\r" $i
		zcashcli generate 1 > /dev/null
	done
	echo ""
}

stop_zcash() {
	if [ -e zcash_pid ]; then kill $(cat zcash_pid); fi
	rm -f zcash_pid
	rm -rf "$ZCASHDIR"
}

cleanup() {
	stop_bitcoin
	stop_zcash
}
