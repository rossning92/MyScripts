import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../libs")
)

from _script import start_script
from _shutil import update_env_var_explorer

update_env_var_explorer()
start_script(file=sys.argv[1])
