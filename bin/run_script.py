import argparse
import os
import sys

sys.path.insert(0, os.path.realpath(
    os.path.dirname(__file__) + '/../libs'))
from _script import *


def to_bool(s):
    return bool(int(s))


parser = argparse.ArgumentParser()
parser.add_argument('--console_title', default=None)
parser.add_argument('--restart_instance', type=to_bool, default=None)
parser.add_argument('--new_window', type=to_bool, default=None)
parser.add_argument('script_name', type=str)
args = parser.parse_args()

update_env_var_explorer()

run_script(args.script_name,
           console_title=args.console_title,
           restart_instance=args.restart_instance,
           new_window=args.new_window)
