#!/bin/bash

# load code from regtestlib
. regtestlib.sh

for arg in $@
do
	case $arg in
		  -z*|--zcashsrc*)
			ZCASHSRC="$2"
			shift
      shift
			;;
      -b*|--bitcoinsrc*)
      BITCOINSRC="$2"
      shift
      shift
      ;;
	esac
done

if [ "${ZCASHSRC}" != "" ]; then echo "Zcash source directory: ${ZCASHSRC}"; fi
if [ "${BITCOINSRC}" != "" ]; then echo "Bitcoin source directory: ${BITCOINSRC}"; fi

trap cleanup EXIT

start_bitcoin
start_zcash

echo "blockchains activated! sleeping foreverish..."
sleep 10000000
