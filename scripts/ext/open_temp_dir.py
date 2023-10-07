import os

from _filemgr import FileManager

if __name__ == "__main__":
    FileManager(os.environ["MY_TEMP_DIR"]).exec()
