import json
import os
import sys

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/../libs"))
from _script import run_script, set_variable, update_env_var_explorer


def try_parse():
    kwargs = {}
    if sys.argv[1].startswith("@"):
        for kvp in sys.argv[1][1:].split(":"):
            k, v = kvp.split("=")
            if v == "1":
                v = True
            elif v == "0":
                v = False
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

run_script(
    file=file, args=rest_args, **kwargs,
)
