# Replace these with your own addresses and trade amts to pass info in through config flag
ADDRS = {
    'regtest': {
        "initiator": {
            "bitcoin": "moAccTjGt6nRCoLKhVLrDCAkqDt7fnsAgC",
            "zcash": "tmJBCsE4ZBcgi2LykoUyei5PDT1cQPkFxpf"
        },
        "fulfiller": {
            "bitcoin": "mxdJ47MeEeqrBDjHj7SrSLFoDuSP3G37t5",
            "zcash": "tmBbe7hWtexP94638H1QUD9Z92BM4ZiXXgA"
        },
        "amounts": {'buy': {'currency': 'zcash', 'amount': 0.02}, 'sell': {'currency': 'bitcoin', 'amount': 0.01}}
    },
    'testnet': {
        "initiator": {
            "bitcoin": "mvc56qCEVj6p57xZ5URNC3v7qbatudHQ9b",
            "zcash": "tmTF7LMLjvEsGdcepWPUsh4vgJNrKMWwEyc"
        },
        "fulfiller": {
            "bitcoin": "mn2boR7rYq9DaAWWrVN5MazHKFyf7UhdyU",
            "zcash": "tmErB22A1G74aq32aAh5AoqgQSJsAAAdT2p"
        },
        "amounts": {'buy': {'currency': 'zcash', 'amount': 0.02}, 'sell': {'currency': 'bitcoin', 'amount': 0.01}}
    }
}

NETWORK = 'testnet'
