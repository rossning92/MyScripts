import os
from pathlib import Path

from _ext import edit_myscript_script
from _script import get_default_script_config_file


if __name__ == "__main__":
    os.chdir("../../")

    script_path = os.environ["_SCRIPT"]
    script_config_file = get_default_script_config_file(script_path)
    if not os.path.exists(script_config_file):
        Path(script_config_file).touch()

    edit_myscript_script(script_config_file)
