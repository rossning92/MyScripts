import os
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import run_script
from _shutil import prepend_to_path, update_env_var_explorer
from utils.logger import setup_logger


def try_parse() -> Tuple[Dict, Optional[str], List[str]]:
    kwargs = {}
    if sys.argv[1].startswith("@"):
        for kvp in sys.argv[1][1:].split(":"):
            k, v = kvp.split("=")
            value: bool | None
            if v == "1":
                value = True
            elif v == "0":
                value = False
            elif v == "auto":
                value = None
            kwargs[k] = value

        rest_args = sys.argv[2:]
    else:
        rest_args = sys.argv[1:]

    if len(rest_args) >= 1:
        file = rest_args[0]
        rest_args = rest_args[1:]
    else:
        file = None

    return kwargs, file, rest_args


if __name__ == "__main__":
    kwargs, file, rest_args = try_parse()

    # If Python is running in a virtual environment (venv), ensure that the
    # shell executes the Python version located inside the venv.
    prepend_to_path(os.path.dirname(sys.executable))

    update_env_var_explorer()

    if kwargs.get("log", None):
        del kwargs["log"]
        setup_logger()

    run_script(
        file=file,
        args=rest_args,
        **kwargs,
    )
