from .actionmenu import ActionMenu


class ConfirmMenu(ActionMenu):
    def __init__(self, prompt="", prompt_color="green", **kwargs):
        super().__init__(
            prompt=prompt + " (y/n)",
            prompt_color=prompt_color,
            search_mode=False,
            **kwargs,
        )
        self.confirmed = False

    @ActionMenu.action(name="Yes", hotkey="y")
    def confirm(self):
        self.confirmed = True
        self.close()

    @ActionMenu.action(name="No", hotkey="n")
    def cancel(self):
        self.confirmed = False
        self.close()

    def on_enter_pressed(self):
        if self.get_selected_index() >= 0:
            super().on_enter_pressed()
        else:
            self.confirm()

    def is_confirmed(self):
        return self.confirmed


def confirm(prompt: str) -> bool:
    menu = ConfirmMenu(prompt=prompt)
    menu.exec()
    return menu.is_confirmed()
