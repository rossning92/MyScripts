import os

from _shutil import shell_open

if __name__ == "__main__":
    shell_open(os.environ["MY_DATA_DIR"])
