import glob
import os
from typing import Optional

from _shutil import get_home_path
from _term import Menu


def select_file() -> Optional[str]:
    files = glob.glob(
        os.path.join(get_home_path(), "Downloads", "**", "*"), recursive=True
    )
    menu = Menu(items=files, label="select file")
    idx = menu.exec()
    if idx >= 0:
        return files[idx]
    else:
        return None
