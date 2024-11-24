import os

from r.open_with.open_with import open_with
from utils.menu.filemenu import FileMenu

if __name__ == "__main__":
    filemgr = FileMenu(os.environ["MY_TEMP_DIR"]).select_file()
    if filemgr is not None:
        open_with(filemgr)
