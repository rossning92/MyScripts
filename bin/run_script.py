import argparse
import os
import sys
import json

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/../libs"))
from _script import run_script, update_env_var_explorer, set_variable


def to_bool(s):
    if s == "None":
        return None

    return bool(int(s))


parser = argparse.ArgumentParser()
parser.add_argument("--console_title", default=None)
parser.add_argument("--restart_instance", type=to_bool, default=None)
parser.add_argument("--new_window", type=to_bool, default=False)
parser.add_argument("file", nargs="?", type=str, default=None)


try:
    delim_pos = sys.argv.index("--")
    main_args = sys.argv[1:delim_pos]
    rest_args = sys.argv[delim_pos + 1 :]
except ValueError:
    main_args = sys.argv[1:]
    rest_args = None

args = parser.parse_args(args=main_args)

update_env_var_explorer()

run_script(
    file=args.file,
    console_title=args.console_title,
    restart_instance=args.restart_instance,
    new_window=args.new_window,
    args=rest_args,
)
