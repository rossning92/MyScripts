import json
import os
import time
from collections import OrderedDict
from typing import List, Optional

from utils.jsonutil import save_json
from utils.menu.dicteditmenu import DictEditMenu

from . import Menu
from .filemenu import FileMenu


def _get_default_preset():
    return {
        "regex": "",
        "sort": False,
    }


class LogMenu(Menu[str]):
    def __init__(
        self,
        files: List[str],
        filter: Optional[str] = None,
        preset_dir: Optional[str] = None,
        wrap_text=False,
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
            else (
                os.environ.get("LOG_PRESET_DIR")
                or os.path.join(os.environ["MY_DATA_DIR"], "log_filters")
            )
        )
        self.__preset_file: Optional[str] = None
        self.__preset = _get_default_preset()

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
            wrap_text=wrap_text,
        )

        self.add_command(self.__clear_logs, hotkey="ctrl+k")
        self.add_command(self.__edit_preset, hotkey="alt+p")
        self.add_command(self.__load_preset, hotkey="ctrl+l")
        self.add_command(self.__save_preset, hotkey="ctrl+s")
        self.add_command(self.__sort)

        if filter:
            self.set_input(filter)

    def __clear_logs(self):
        self.__lines.clear()
        self.refresh()

    def __edit_preset(self):
        DictEditMenu(self.__preset, default_dict=_get_default_preset()).exec()
        if self.__preset_file:
            save_json(self.__preset_file, self.__preset)

    def __load_preset(self):
        menu = FileMenu(
            prompt="select preset",
            goto=self.preset_dir,
            show_size=False,
            recursive=True,
            allow_cd=False,
        )
        self.__preset_file = menu.select_file()
        if self.__preset_file:
            with open(self.__preset_file, "r", encoding="utf-8") as f:
                self.__preset = {**_get_default_preset(), **json.load(f)}

            assert isinstance(self.__preset["regex"], str)
            self.set_input(self.__preset["regex"])

            if self.__preset.get("sort"):
                self.__sort()

            if self.__preset.get("highlight"):
                self.__log_highlight.clear()
                self.__log_highlight.update(self.__default_log_highlight)
                assert isinstance(self.__preset["regex"], dict)
                self.__log_highlight.update(self.__preset["highlight"])

        self.update_screen()

    def __save_preset(self):
        menu = FileMenu(
            prompt="save preset",
            goto=self.preset_dir,
            show_size=False,
            allow_cd=False,
        )
        menu.select_file()
        file_name = menu.get_input()
        if file_name:
            if not file_name.endswith(".json"):
                file_name += ".json"
            self.__preset_file = os.path.join(self.preset_dir, file_name)
            save_json(self.__preset_file, self.__preset)

    def __sort(self):
        self.__lines.sort()
        self.refresh()

    def on_enter_pressed(self):
        self.__preset["regex"] = self.get_input()
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
                while not self.is_closed():
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
