from utils.clip import get_clip

from ..menu import Menu


class Input(Menu):
    def __init__(self):
        super().__init__(prompt=">", items=[get_clip()])

    def input(self) -> str:
        self.exec()
        return self.get_input()
