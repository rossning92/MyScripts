import os
import time
from typing import List, Optional

from . import Menu


class LogViewerMenu(Menu[str]):
    def __init__(self, file: str, filter: Optional[str] = None):
        self.__file = file
        self.__file_name = os.path.basename(file)
        self.__lines: List[str] = []
        super().__init__(
            prompt="/",
            items=self.__lines,
            text_color_map=[
                (r" D |\bDEBUG\b", "blue"),
                (r" W |\bWARN\b", "yellow"),
                (r" (E|F) |\bERROR\b|>>>", "red"),
            ],
            close_on_selection=False,
            cancellable=False,
            fuzzy_search=False,
        )
        self.add_command(self.sort)

        if filter:
            self.set_input(filter)

    def sort(self):
        self.__lines.sort()
        self.refresh()

    def on_enter_pressed(self):
        self._selected_row = self._matched_item_indices[self._selected_row]
        self.set_input("")

    def get_status_bar_text(self):
        return self.__file_name + " | " + super().get_status_bar_text()

    def on_created(self):
        last_update = 0.0

        with open(self.__file, "r", encoding="utf-8", errors="replace") as f:
            while not self._closed:
                line = f.readline()
                if line == "":
                    self.process_events(timeout_ms=1000)

                else:
                    self.append_item(line.rstrip("\n"))

                    now = time.time()
                    if now - last_update > 0.1:
                        last_update = now
                        self.process_events()
