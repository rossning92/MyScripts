import os

from utils.menu.filemenu import FileMenu

if __name__ == "__main__":
    FileMenu(os.environ["MY_DATA_DIR"]).exec()
