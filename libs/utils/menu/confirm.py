from ..menu.actionmenu import ActionMenu


class ConfirmMenu(ActionMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__confirmed = False

    @ActionMenu.action(hotkey="y")
    def confirm(self):
        self.__confirmed = True
        self.close()

    @ActionMenu.action(hotkey="n")
    def cancel(self):
        self.__confirmed = False
        self.close()

    def is_confirmed(self):
        return self.__confirmed


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.is_confirmed()
