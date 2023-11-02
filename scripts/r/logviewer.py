import argparse
import os
import time
from typing import List

from utils.menu import Menu

log_filter_dir = os.path.join(os.environ["MY_DATA_DIR"], "log_filters")


class _LogMenu(Menu[str]):
    def __init__(
        self,
        file: str,
    ):
        self.__file = file
        self.__lines: List[str] = []
        super().__init__(
            prompt=os.path.basename(file),
            items=self.__lines,
            text_color_map={
                " D ": "blue",
                " W ": "yellow",
                " (E|F) ": "red",
            },
            close_on_selection=False,
            cancellable=False,
            fuzzy_search=False,
        )

        self.add_hotkey("ctrl+f", lambda: self.filter_logs())

    def filter_logs(self):
        m = _FilterMenu()
        m.exec()
        filter_name = m.get_selected_item()
        if filter_name:
            with open(
                os.path.join(log_filter_dir, f"{filter_name}.txt"),
                "r",
                encoding="utf-8",
            ) as f:
                self.set_input(f.read())

    def on_created(self):
        last_update = 0.0

        with open(self.__file, "r", encoding="utf-8") as f:
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


class _FilterMenu(Menu[str]):
    def __init__(self):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", default=None, type=str)
    args = parser.parse_args()

    _LogMenu(file=args.file).exec()
