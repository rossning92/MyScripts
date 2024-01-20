import datetime

from utils.menu.actionmenu import ActionMenu


class MyActionMenu(ActionMenu):
    @ActionMenu.action(hotkey="ctrl+k")
    def hello(self):
        input("Hello!\n(press enter to exit...)")

    def on_idle(self):
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.set_message(current_time)


if __name__ == "__main__":
    MyActionMenu().exec()
