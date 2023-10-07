from _clip import get_clip

from ..menu import Menu


class Input(Menu):
    def __init__(self):
        super().__init__(label="keyword", items=[get_clip()])

    def input(self) -> str:
        self.exec()
        return self.get_input()
