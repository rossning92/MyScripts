from ..menu import Menu


class ConfirmMenu(Menu):
    def __init__(self, prompt) -> None:
        super().__init__(
            allow_input=False,
            items=["[y] yes", "[n] no"],
            prompt=prompt,
        )

        self.add_hotkey("y", self.confirm)
        self.add_hotkey("n", self.cancel)

    def confirm(self):
        self.set_selected_row(0)
        self.close()

    def cancel(self):
        self.set_selected_row(1)
        self.close()


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.get_selected_index() == 0
