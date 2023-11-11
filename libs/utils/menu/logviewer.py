import os
import time
from typing import List, Optional

from . import Menu


class _SelectFilterMenu(Menu[str]):
    def __init__(self, log_filter_dir: str):
        log_filters = (
            [
                os.path.splitext(f)[0]
                for f in os.listdir(log_filter_dir)
                if f.endswith(".txt")
            ]
            if os.path.isdir(log_filter_dir)
            else []
        )

        super().__init__(
            items=log_filters,
            prompt="/",
        )


class LogViewerMenu(Menu[str]):
    def __init__(self, file: str, filter: Optional[str] = None):
        self.__file = file
        self.__file_name = os.path.basename(file)
        self.__lines: List[str] = []
        self.log_filter_dir = os.path.join(os.environ["MY_DATA_DIR"], "log_filters")

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
        self.add_command(lambda: self.filter_logs(), hotkey="ctrl+f")

        if filter:
            self.set_input(filter)

    def filter_logs(self):
        m = _SelectFilterMenu(log_filter_dir=self.log_filter_dir)
        m.exec()
        filter_name = m.get_selected_item()
        if filter_name:
            with open(
                os.path.join(self.log_filter_dir, f"{filter_name}.txt"),
                "r",
                encoding="utf-8",
            ) as f:
                self.set_input(f.read())

    def sort(self):
        self.__lines.sort()
        self.refresh()

    def on_enter_pressed(self):
        if self._selected_row < len(self._matched_item_indices):
            self._selected_row = self._matched_item_indices[self._selected_row]
            self.set_input("")

    def get_status_bar_text(self):
        return self.__file_name + " | " + super().get_status_bar_text()

    def on_created(self):
        last_update = 0.0
        last_file_size = 0
        with open(self.__file, "r", encoding="utf-8", errors="replace") as f:
            while not self._closed:
                line = f.readline()
                if line == "":
                    self.process_events(timeout_ms=1000)
                    file_size = os.path.getsize(self.__file)
                    if file_size < last_file_size:
                        f.seek(0)
                        self.clear_items()
                    last_file_size = file_size

                else:
                    self.append_item(line.rstrip("\n"))

                    now = time.time()
                    if now - last_update > 0.1:
                        last_update = now
                        self.process_events()
