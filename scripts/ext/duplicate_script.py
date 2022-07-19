import os

from _ext import edit_myscript_script, enter_script_path
from _shutil import copy

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.join(script_dir, ".."))

    script_path = enter_script_path()

    if script_path:
        dir_name = os.path.dirname(script_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        src_script = os.getenv("SCRIPT")
        copy(src_script, script_path)

        edit_myscript_script(os.path.realpath(script_path))
