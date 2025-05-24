from typing import Optional

from . import Menu


class TextMenu(Menu[str]):
    def __init__(
        self, text: Optional[str] = None, file: Optional[str] = None, **kwargs
    ):
        super().__init__(
            close_on_selection=False,
            cancellable=True,
            fuzzy_search=False,
            search_on_enter=True,
            **kwargs
        )
        if file:
            with open(file, "r", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    self.items.append(line)
        elif text:
            for line in text.splitlines():
                self.items.append(line)
        else:
            raise Exception("Either `file` or `text` needs to be provided")

    def on_enter_pressed(self):
        if self.search_by_input():
            return
        else:
            self.clear_input()
