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

        return kwargs, sys.argv[2], sys.argv[3:]
    else:
        return {}, sys.argv[1], sys.argv[2:]


kwargs, file, rest_args = try_parse()


update_env_var_explorer()

run_script(
    file=file, args=rest_args, new_window=False, **kwargs,
)
