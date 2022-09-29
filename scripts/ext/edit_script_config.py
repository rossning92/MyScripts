import os

from _ext import edit_script_config

if __name__ == "__main__":
    edit_script_config(script_path=os.environ["SCRIPT"])
