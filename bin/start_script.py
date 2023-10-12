import argparse
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import start_script
from _shutil import get_env_bool, update_env_var_explorer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()

    selected_files = update_env_var_explorer()
    start_script(
        file=args.file,
        args=args.args if args.args else selected_files,
        restart_instance=get_env_bool("RESTART_INSTANCE"),
    )
