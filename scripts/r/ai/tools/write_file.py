import os

from ai.tools import Settings
from utils.checkpoints import backup_files
from utils.menu.confirmmenu import confirm


def write_file(file: str, content: str):
    """
    Write content to a file at the specified path.
    - If the file already exists, the original content will be overwritten.
    """

    if Settings.need_confirm and not confirm(f"Write to file: `{file}`?"):
        raise KeyboardInterrupt("File write operation was canceled by the user")

    if os.path.exists(file):
        backup_files([file])

    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
