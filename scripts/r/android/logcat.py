from _android import logcat
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--pkg", default=None)
args = parser.parse_args()

logcat(proc_name=args.pkg)
