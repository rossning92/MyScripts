import argparse
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import start_script
from _shutil import get_env_bool, prepend_to_path, update_env_var_explorer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    # If Python is running in a virtual environment (venv), ensure that the
    # shell executes the Python version located inside the venv.
    prepend_to_path(os.path.dirname(sys.executable))

    selected_files = update_env_var_explorer()

    start_script(
        file=args.file,
        args=args.args if args.args else selected_files,
        restart_instance=get_env_bool("RESTART_INSTANCE"),
    )
