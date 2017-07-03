import argparse, textwrap
from utils import *
import database as db

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent('''\
                == Contracts ==
                importcontract "hexstr" - import an existing trade from a hex string
                exportcontract - (not implemented) export the data of an existing xcat trade as a hex string

                '''))
    parser.add_argument("-importcontract", type=str, action="store", help="import an existing trade from a hex string.")
    args = parser.parse_args()

    if args.importcontract:
        hexstr = args.importcontract
        db.create(hexstr)
