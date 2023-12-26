from utils.menu.actionmenu import ActionMenu

menu = ActionMenu()


@menu.action(hotkey="ctrl+k")
def hello():
    input("Hello!\n(press enter to exit...)")


if __name__ == "__main__":
    menu.exec()
