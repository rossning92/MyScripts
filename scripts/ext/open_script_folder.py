import os

from utils.menu.filemgr import FileManager

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]
    FileManager(goto=script_path).exec()
