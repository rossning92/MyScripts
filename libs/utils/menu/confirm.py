from ..menu import Menu


class ConfirmMenu(Menu):
    def __init__(self, prompt) -> None:
        super().__init__(
            allow_input=False,
            items=["yes (y)", "no (n)"],
            prompt=prompt,
        )

        self.__confirmed = False
        self.add_command(self.confirm, hotkey="y")
        self.add_command(self.cancel, hotkey="n")

    def confirm(self):
        self.__confirmed = True
        self.close()

    def cancel(self):
        self.close()

    def is_confirmed(self):
        if self.get_selected_index() == 0:
            return True
        else:
            return self.__confirmed


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.is_confirmed()
