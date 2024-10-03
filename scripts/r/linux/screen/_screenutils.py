import subprocess
from typing import Optional

from utils.menu import Menu


def select_screen() -> Optional[str]:
    out = subprocess.check_output(["screen", "-ls"], universal_newlines=True)
    lines = out.splitlines()
    print(lines)
    lines = [x.strip() for x in lines if x.startswith("\t")]
    m = Menu(items=lines)
    m.exec()
    selected = m.get_selected_item()
    if selected is not None:
        id = selected.split(".")[0]
        return id
    else:
        return None
