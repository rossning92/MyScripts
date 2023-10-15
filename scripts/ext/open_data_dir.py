import os

from utils.menu.filemgr import FileManager

if __name__ == "__main__":
    FileManager(os.environ["MY_DATA_DIR"]).exec()
