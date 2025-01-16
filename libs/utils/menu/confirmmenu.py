from . import Menu


class ConfirmMenu(Menu):
    def __init__(self, prompt="", **kwargs):
        super().__init__(prompt=prompt + " (y/n)", **kwargs)
        self.__confirmed = False
        self.add_command(self.__confirm, hotkey="y")
        self.add_command(self.__cancel, hotkey="n")

    def __confirm(self):
        self.__confirmed = True
        self.close()

    def __cancel(self):
        self.__confirmed = False
        self.close()

    def on_enter_pressed(self):
        self.__confirm()

    def is_confirmed(self):
        return self.__confirmed


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.is_confirmed()
