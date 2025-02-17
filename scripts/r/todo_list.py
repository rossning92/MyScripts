import argparse
import os
from datetime import datetime
from typing import Any, Dict

import dateutil.parser
from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputmenu import InputMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


def _parse_date(s: str) -> datetime:
    return dateutil.parser.parse(s, ignoretz=True)


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        super().__init__(json_file=data_file)

        self.__sort_tasks()

        self.add_command(self.__edit_due, hotkey="alt+d")
        self.add_command(self.__edit_description, hotkey="ctrl+e")
        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__reload, hotkey="ctrl+r")
        self.add_command(self.__toggle_status, hotkey="ctrl+x")

    def get_item_text(self, item: TodoItem) -> str:
        date = _parse_date(item["due"])

        # Calculate the relative difference and convert to appropriate unit
        now = datetime.now(date.tzinfo)
        diff = (date - now).days
        if abs(diff) > 365:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff // 365}yr"
        elif abs(diff) > 30:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff // 30}mo"
        elif abs(diff) != 0:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff}d"
        else:
            time_diff_str = ""

        if date.hour == 0 and date.minute == 0:
            date_str = date.strftime("%y-%m-%d").ljust(14)
        else:
            date_str = date.strftime("%y-%m-%d %H:%M")

        return (
            ("[x]" if item["done"] else "[ ]")
            + " "
            + f"{time_diff_str:>5}"
            + " "
            + date_str
            + " "
            + item["description"]
        )

    def get_item_color(self, item: Any) -> str:
        due = _parse_date(item["due"])
        now = datetime.now()
        if item["done"]:
            return "blue"
        elif due < now:
            return "red"
        else:
            return "white"

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def __edit_due(self):
        selected = self.get_selected_item()
        if selected:
            val = InputMenu(prompt="due", text=selected["due"]).request_input()
            if val is not None and val != selected["due"]:
                selected["due"] = val
                self.save_json()

    def __edit_description(self):
        selected = self.get_selected_item()
        if selected:
            new_text = self.call_func_without_curses(
                lambda: edit_text(selected["description"])
            )
            if new_text != selected["description"]:
                selected["description"] = new_text
                self.save_json()
                self.update_screen()

    def __new_task(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        todo_item = {"due": current_date, "done": False, "description": ""}
        self.items.append(todo_item)
        self.__edit_todo_item(todo_item)

    def __reload(self):
        self.load_json()
        self.__sort_tasks()
        self.set_message("reloaded")

    def __sort_tasks(self):
        self.items.sort(key=lambda item: item.get("due"), reverse=True)

    def __toggle_status(self):
        selected = self.get_selected_item()
        if selected:
            selected["done"] = False if selected["done"] else True
            self.save_json()
            self.update_screen()

    def __edit_todo_item(self, item: TodoItem):
        DictEditMenu(
            item,
            on_dict_update=lambda _: self.save_json(),
        ).exec()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_file",
        type=str,
        nargs="?",
        help="Path to todo list data file",
        default=os.environ.get("TODO_DATA_FILE"),
    )
    args = parser.parse_args()

    menu = TodoMenu(args.data_file)
    menu.exec()


if __name__ == "__main__":
    main()
