import json
import os
import time
from collections import OrderedDict
from typing import List, Optional

from . import Menu
from .inputmenu import InputMenu


class _SelectPresetMenu(Menu[str]):
    def __init__(self, preset_dir: str):
        preset_names = (
            [
                os.path.splitext(f)[0]
                for f in os.listdir(preset_dir)
                if f.endswith(".json")
            ]
            if os.path.isdir(preset_dir)
            else []
        )

        super().__init__(
            items=preset_names,
            prompt="load preset",
        )


class LogMenu(Menu[str]):
    def __init__(
        self,
        files: List[str],
        filter: Optional[str] = None,
        preset_dir: Optional[str] = None,
    ):
        self.__files = files
        self.__file_name = (
            os.path.basename(self.__files[0])
            if len(self.__files) == 1
            else "[multiple]"
        )
        self.__lines: List[str] = []
        self.preset_dir = (
            preset_dir
            if preset_dir
            else os.path.join(os.environ["MY_DATA_DIR"], "log_filters")
        )

        self.__default_log_highlight: OrderedDict[str, str] = OrderedDict()
        self.__default_log_highlight[r" D |\b(DEBUG|Debug|debug)\b"] = "blue"
        self.__default_log_highlight[r" W |\b(WARN|Warn(ing)?|warn(ing)?)\b"] = "yellow"
        self.__default_log_highlight[r" (E|F) |\b(ERROR|Error|error|err)\b"] = "red"
        self.__default_log_highlight[">>>|success"] = "green"
        self.__log_highlight = self.__default_log_highlight.copy()

        super().__init__(
            items=self.__lines,
            highlight=self.__log_highlight,
            close_on_selection=False,
            cancellable=True,
            fuzzy_search=False,
            search_on_enter=True,
        )

        self.add_command(self.__clear_logs, hotkey="ctrl+k")
        self.add_command(self.__load_preset, hotkey="ctrl+l")
        self.add_command(self.__save_preset, hotkey="ctrl+s")
        self.add_command(self.__sort)

        if filter:
            self.set_input(filter)

    def __clear_logs(self):
        self.__lines.clear()
        self.refresh()

    def __load_preset(self):
        m = _SelectPresetMenu(preset_dir=self.preset_dir)
        m.exec()
        preset_name = m.get_selected_item()
        if preset_name:
            preset_file = os.path.join(self.preset_dir, f"{preset_name}.json")
            with open(preset_file, "r", encoding="utf-8") as f:
                preset = json.load(f)

            self.set_input(preset["regex"])

            if "sort" in preset and preset["sort"]:
                self.__sort()

            if "highlight" in preset:
                self.__log_highlight.clear()
                self.__log_highlight.update(self.__default_log_highlight)
                self.__log_highlight.update(preset["highlight"])

        self.update_screen()

    def __save_preset(self):
        filter = self.get_input()
        if filter:
            preset_name = InputMenu(prompt="save preset").request_input()
            if preset_name:
                preset_file = os.path.join(self.preset_dir, f"{preset_name}.json")
                with open(preset_file, "w", encoding="utf-8") as f:
                    json.dump({"regex": filter}, f, indent=2, ensure_ascii=False)
        self.update_screen()

    def __sort(self):
        self.__lines.sort()
        self.refresh()

    def on_enter_pressed(self):
        if self.search_by_input():
            return

        else:
            self.clear_input()

    def get_status_bar_text(self):
        cols = [self.__file_name]
        text = super().get_status_bar_text()
        if text:
            cols.append(text)
        return " | ".join(cols)

    def on_created(self):
        last_update = 0.0
        if len(self.__files) == 1:
            last_file_size = 0
            with open(self.__files[0], "r", encoding="utf-8", errors="replace") as f:
                while not self._closed:
                    line = f.readline()
                    if line == "":
                        self.process_events(timeout_sec=1.0)
                        file_size = os.path.getsize(self.__files[0])
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
        else:
            for file in self.__files:
                file_name = os.path.basename(file)
                with open(file, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.read().splitlines()
                    for line in lines:
                        self.append_item(file_name + ": " + line)
                    now = time.time()
                    if now - last_update > 0.1:
                        last_update = now
                        self.process_events()
