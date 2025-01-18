import subprocess
from typing import Optional

from utils.menu import Menu
from utils.menu.confirmmenu import confirm


def _select_distro() -> Optional[str]:
    output = subprocess.check_output(
        ["wsl", "-l", "-v"]
    )  # wsl will output using utf-16 encoding
    lines = output.decode("utf-16").splitlines()
    menu = Menu(items=lines)
    menu.exec()
    selected = menu.get_selected_item()
    if not selected:
        return None

    distro = selected.lstrip("*").split()[0]
    return distro


def _main():
    distro = _select_distro()
    if distro and confirm("confirm remove distro"):
        subprocess.check_call(["wsl", "--unregister", distro])


if __name__ == "__main__":
    _main()
