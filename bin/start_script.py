import argparse
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import start_script
from _shutil import prepend_to_path, update_env_var_explorer


def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif value.lower() in ("no", "false", "f", "n", "0"):
        return False
    elif value is None:
        return None
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("--cd", type=str2bool, default=True)
    parser.add_argument("--restart-instance", type=str2bool, default=None)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    # If Python is running in a virtual environment (venv), ensure that the
    # shell executes the Python version located inside the venv.
    prepend_to_path(os.path.dirname(sys.executable))

    selected_files = update_env_var_explorer()

    start_script(
        file=args.file,
        args=args.args if args.args else selected_files,
        cd=args.cd,
        restart_instance=args.restart_instance,
    )
