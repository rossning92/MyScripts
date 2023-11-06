from ..menu import Menu


class ConfirmMenu(Menu):
    def __init__(self, prompt) -> None:
        super().__init__(
            allow_input=False,
            items=["[y] yes", "[n] no"],
            prompt=prompt,
        )

        self.confirmed = False
        self.add_command(self.confirm, hotkey="y")
        self.add_command(self.cancel, hotkey="n")

    def confirm(self):
        self.confirmed = True
        self.close()

    def cancel(self):
        self.close()


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.confirmed
