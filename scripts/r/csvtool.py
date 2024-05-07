import argparse
import sys

import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "command", help="The calculation to perform", choices=["mean", "avg", "median"]
)
parser.add_argument("cols", metavar="N", type=str, nargs="*", help="column names")
args = parser.parse_args()


df = pd.read_csv(sys.stdin, header=0)
if args.command == "mean":
    result = df[args.cols[0]].mean()
    print(result)
