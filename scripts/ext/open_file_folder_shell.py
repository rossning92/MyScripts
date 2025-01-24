import os

from utils.shutil import shell_open

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]
    shell_open(os.path.dirname(script_path))
