import subprocess

from utils.menu import Menu
from utils.menu.actionmenu import ActionMenu


class ContainerMenu(ActionMenu):
    def __init__(self, container: str):
        super().__init__()
        self.__container = container

    @ActionMenu.action()
    def delete_container(self):
        subprocess.check_output(["docker", "rm", "-f", self.__container])


if __name__ == "__main__":
    lines = subprocess.check_output(
        ["docker", "ps", "-a"], universal_newlines=True
    ).splitlines()
    menu = Menu(items=lines, selected_index=1)
    menu.exec()
    selected = menu.get_selected_item()
    if selected is not None:
        container = selected.split()[0]
        container_menu = ContainerMenu(container=container)
        container_menu.exec()
