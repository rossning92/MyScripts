from _android import adb_shell
from _shutil import menu_item, menu_loop


@menu_item(key="a")
def activities():
    adb_shell("dumpsys activity activities | grep -E 'Stack #|\* '", echo=True)


if __name__ == "__main__":
    menu_loop()
