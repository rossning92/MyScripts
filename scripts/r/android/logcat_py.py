import argparse

from utils.android import logcat

parser = argparse.ArgumentParser()
parser.add_argument("--pkg", default=None)
args = parser.parse_args()

logcat(pkg=args.pkg)
