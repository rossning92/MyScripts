import os

from utils.editor import open_code_editor

if __name__ == "__main__":
    cwd = os.path.realpath(".")
    open_code_editor(cwd)
