import os

from utils.editor import open_in_vim
from utils.script.path import get_data_dir

if __name__ == "__main__":
    open_in_vim(os.path.join(get_data_dir(), ".env"))
