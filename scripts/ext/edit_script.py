import os

from _ext import edit_myscript_script
from _shutil import print2

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"].strip()
    print2("Edit Script: " + script_path)
    edit_myscript_script(script_path)
