import os
import subprocess
import sys

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import run_script
from _shutil import update_env_var_explorer


def try_parse():
    kwargs = {}
    if sys.argv[1].startswith("@"):
        for kvp in sys.argv[1][1:].split(":"):
            k, v = kvp.split("=")
            if v == "1":
                v = True
            elif v == "0":
                v = False
            elif v == "auto":
                v = None
            kwargs[k] = v

        rest_args = sys.argv[2:]
    else:
        rest_args = sys.argv[1:]

    if len(rest_args) >= 1:
        file = rest_args[0]
        rest_args = rest_args[1:]
    else:
        file = None

    return kwargs, file, rest_args


kwargs, file, rest_args = try_parse()

update_env_var_explorer()

if "cd" not in kwargs:
    kwargs["cd"] = False

# setup_logger()

try:
    run_script(
        file=file,
        args=rest_args,
        **kwargs,
    )
except subprocess.CalledProcessError as ex:
    print(ex)
    sys.exit(1)
