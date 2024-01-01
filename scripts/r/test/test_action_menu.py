from utils.menu.actionmenu import ActionMenu


class MyActionMenu(ActionMenu):
    @ActionMenu.action(hotkey="ctrl+k")
    def hello(self):
        input("Hello!\n(press enter to exit...)")


if __name__ == "__main__":
    MyActionMenu().exec()
