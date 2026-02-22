import glob
import os

from utils.editor import open_code_editor
from utils.menu import Menu
from utils.script.path import get_my_script_root


def _main():
    root = get_my_script_root()
    files = [
        file.replace(root + os.path.sep, "")
        for file in glob.glob(os.path.join(root, "**", "*"), recursive=True)
        if os.path.isfile(file) and "node_modules" not in file
    ]
    menu = Menu(items=files)
    menu.exec()
    selected = menu.get_selected_item()
    if selected is not None:
        file_full_path = os.path.join(root, selected)
        open_code_editor(file_full_path)


if __name__ == "__main__":
    _main()
