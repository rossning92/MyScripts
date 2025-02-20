import argparse
import os
from datetime import datetime
from typing import Any, Dict, Optional

import dateutil.parser
from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputmenu import InputMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


DUE_DATE_FIELD = "due"
IMPORTANT_FIELD = "important"


def _parse_date(s: str) -> Optional[datetime]:
    try:
        return dateutil.parser.parse(s, ignoretz=True)
    except dateutil.parser.ParserError:
        return None


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        super().__init__(json_file=data_file, backup_json=True)

        self.__sort_tasks()

        self.add_command(self.__edit_description, hotkey="ctrl+e")
        self.add_command(self.__edit_due, hotkey="alt+d")
        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__reload, hotkey="ctrl+r")
        self.add_command(self.__toggle_important, hotkey="!")
        self.add_command(self.__toggle_status, hotkey="ctrl+x")

    def __set_selected_item_value(self, name, value: Any):
        selected = self.get_selected_item()
        if selected:
            if value is None:
                del selected[name]
            else:
                selected[name] = value
            self.save_json()
            self.update_screen()

    def __toggle_important(self):
        selected = self.get_selected_item()
        if selected:
            if selected.get(IMPORTANT_FIELD):
                self.__set_selected_item_value(IMPORTANT_FIELD, None)
            else:
                self.__set_selected_item_value(IMPORTANT_FIELD, True)

    def get_item_text(self, item: TodoItem) -> str:
        date_str = ""
        time_diff_str = ""
        if item.get(DUE_DATE_FIELD):
            date = _parse_date(item[DUE_DATE_FIELD])
            if date:
                now = datetime.now(date.tzinfo)
                diff = (date - now).days
                if abs(diff) > 365:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff // 365}yr"
                elif abs(diff) > 30:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff // 30}mo"
                elif abs(diff) != 0:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff}d"

                if date.hour == 0 and date.minute == 0:
                    date_str = date.strftime("%m-%d").ljust(11)
                else:
                    date_str = date.strftime("%m-%d %H:%M")

        return (
            ("[x]" if item["done"] else "[ ]")
            + (" ! " if item.get(IMPORTANT_FIELD) else "   ")
            + " "
            + f"{time_diff_str:>5} {date_str:<11}"
            + " "
            + item["description"]
        )

    def get_item_color(self, item: Any) -> str:
        now = datetime.now()
        if item["done"]:
            return "blue"

        if item.get(IMPORTANT_FIELD):
            return "yellow"

        due = item.get(DUE_DATE_FIELD)
        if due:
            due_date = _parse_date(due)
            if due_date and due_date < now:
                return "red"

        return "white"

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def __edit_due(self):
        selected = self.get_selected_item()
        if selected:
            val = InputMenu(
                prompt=DUE_DATE_FIELD, text=selected.get(DUE_DATE_FIELD, "")
            ).request_input()
            if val is not None and val != selected.get(DUE_DATE_FIELD, ""):
                selected[DUE_DATE_FIELD] = val
                self.save_json()

    def __edit_item_description(self, item: TodoItem):
        new_text = self.call_func_without_curses(lambda: edit_text(item["description"]))
        if new_text != item["description"]:
            item["description"] = new_text
            self.save_json()
            self.update_screen()

    def __edit_description(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_item_description(selected)

    def __new_task(self):
        # current_date = datetime.now().strftime("%Y-%m-%d")
        item = {"done": False, "description": ""}
        self.items.append(item)
        self.__edit_item_description(item)

    def __reload(self):
        self.load_json()
        self.__sort_tasks()
        self.set_message("reloaded")

    def __sort_tasks(self):
        self.items.sort(
            key=lambda item: (item.get(DUE_DATE_FIELD, ""), item.get("description")),
            reverse=True,
        )

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
        "--data-file",
        type=str,
        help="Path to todo list data file",
        default=os.environ.get("TODO_DATA_FILE"),
    )
    args = parser.parse_args()

    menu = TodoMenu(data_file=args.data_file)
    menu.exec()


if __name__ == "__main__":
    main()
