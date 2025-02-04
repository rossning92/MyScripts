import subprocess

from chocopkgmenu import ChocoPackageMenu
from utils.menu.confirmmenu import confirm

if __name__ == "__main__":
    menu = ChocoPackageMenu()
    menu.exec()
    package = menu.get_selected_package()
    if package and confirm(f"uninstall `{package}`?"):
        subprocess.check_call(
            [
                "choco",
                "uninstall",
                package,
                "-y",
                "-n",
                "--skipautouninstaller",
            ]
        )
