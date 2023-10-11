import os

from _filemgr import FileManager
from r.open_with.open_with import open_with

if __name__ == "__main__":
    filemgr = FileManager(os.environ["MY_TEMP_DIR"]).select_file()
    if filemgr is not None:
        open_with(filemgr)
