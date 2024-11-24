import os

from utils.menu.filemenu import FileMenu

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]
    FileMenu(goto=script_path).exec()
