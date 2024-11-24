from . import Menu


class TextMenu(Menu[str]):
    def __init__(self, file: str, **kwargs):
        super().__init__(
            close_on_selection=False,
            cancellable=True,
            fuzzy_search=False,
            search_on_enter=True,
            **kwargs
        )
        with open(file, "r", encoding="utf-8") as f:
            for line in f.read().splitlines():
                self.items.append(line)

    def on_enter_pressed(self):
        if self.search_by_input():
            return
        else:
            self.clear_input()
