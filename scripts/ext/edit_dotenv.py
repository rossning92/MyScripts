import os

from scripting.path import get_data_dir
from utils.editor import open_in_vim

if __name__ == "__main__":
    open_in_vim(os.path.join(get_data_dir(), ".env"))
