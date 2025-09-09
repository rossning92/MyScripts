import argparse
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

from utils.dateutil import format_timestamp
from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputdatemenu import input_date
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


_DUE_TIMESTAMP = "due_ts"
_STATUS = "status"


_status_symbols = {"closed": "[x]", "in_progress": "[=]", "none": "[ ]"}


def get_pretty_ts(ts):
    time_diff_str = ""
    date_str = format_timestamp(ts, include_year=False).ljust(11)

    date = datetime.fromtimestamp(ts)
    if date:
        now = datetime.now(date.tzinfo)
        diff = (date.date() - now.date()).days
        sign = "+" if diff > 0 else "-"
        total_days = abs(diff)
        if total_days > 365:
            years, remainder = divmod(total_days, 365)
            months = remainder // 30
            month_str = f"{months}M" if months > 0 else ""
            time_diff_str = f"{sign}{years}y{month_str}"
        elif total_days > 30:
            months, days = divmod(total_days, 30)
            day_str = f"{days}d" if days > 0 else ""
            time_diff_str = f"{sign}{months}M{day_str}"
        elif total_days != 0:
            time_diff_str = f"{sign}{total_days}d"
        elif total_days == 0:
            time_diff_str = "today"
    return f"{time_diff_str:>7} {date_str}"


class _EditTodoItemMenu(DictEditMenu):
    def edit_dict_value(self, data: Dict[str, Any], name: str):
        if name in (_DUE_TIMESTAMP,):
            ts = input_date(
                prompt=name,
                default_ts=data[name],
            )
            if ts:
                data[name] = ts
        else:
            return super().edit_dict_value(data, name)

    def get_value_str(self, name: str, val: Any) -> str:
        if name in (_DUE_TIMESTAMP,):
            return format_timestamp(val)
        else:
            return super().get_value_str(name, val)


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        self.__last_reload_check_time = 0.0

        super().__init__(json_file=data_file, backup_json=True)

        self.__sort_tasks()

        self.add_command(self.__duplicate_task, hotkey="ctrl+d")
        self.add_command(self.__edit_description, hotkey="ctrl+e")
        self.add_command(self.__edit_due, hotkey="alt+d")
        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__reload, hotkey="ctrl+r")
        self.add_command(self.__set_status_wip, hotkey="alt+w")
        self.add_command(self.__toggle_status, hotkey="alt+x")

    def __duplicate_task(self):
        selected = self.get_selected_item()
        if selected:
            copy = selected.copy()
            copy[_STATUS] = "none"
            self.items.append(copy)
            self.__edit_todo_item(copy)

    def __set_selected_item_value(self, kvps: Dict[str, Any]):
        selected = self.get_selected_item()
        if selected:
            for name, value in kvps.items():
                if value is None:
                    del selected[name]
                else:
                    selected[name] = value
            self.save_json()
            self.update_screen()

    def __toggle_status(self):
        selected = self.get_selected_item()
        if selected:
            if selected.get(_STATUS) != "closed":
                self.__set_selected_item_value({_STATUS: "closed"})
            else:
                self.__set_selected_item_value({_STATUS: "none"})

    def get_item_text(self, item: TodoItem) -> str:
        # Date
        if item.get(_DUE_TIMESTAMP):
            date = get_pretty_ts(item[_DUE_TIMESTAMP])
        else:
            date = ""

        # Description
        desc_lines = item["description"].splitlines()
        desc = desc_lines[0] + " ..." if len(desc_lines) > 1 else desc_lines[0]

        return _status_symbols[item[_STATUS]] + " " + f"{date:<19}" + " " + desc

    def get_item_color(self, item: Any) -> str:
        now = datetime.now()
        if item[_STATUS] == "in_progress":
            return "green"
        elif item[_STATUS] == "closed":
            return "blue"

        due = item.get(_DUE_TIMESTAMP)
        if due:
            due_date = datetime.fromtimestamp(item[_DUE_TIMESTAMP])
            if due_date and due_date < now:
                return "red"

        return "white"

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def on_idle(self):
        now = time.time()
        if now > self.__last_reload_check_time + 1.0:
            self.__last_reload_check_time = now
            self.__reload(sort=False)

    def on_escape_pressed(self):
        if not self.clear_input():
            if len(self.items) > 0:
                self.set_selected_item(self.items[0])

    def save_json(self):
        try:
            super().save_json()
        except Exception as e:
            self.set_message(f"Error on saving: {e}")

    def load_json(self) -> bool:
        try:
            return super().load_json()
        except Exception as e:
            self.set_message(f"Error on loading: {e}")
            return False

    def __edit_timestamp_field(self, item: TodoItem, field_name: str):
        ts = input_date(
            prompt=field_name,
            default_ts=item[field_name] if field_name in item else None,
        )
        if ts is None:
            return

        if ts == item.get(field_name, 0):
            self.set_message("Skip updating the same date")
            return

        if ts <= 0.0:
            del item[field_name]
            self.set_message(f"Reset {field_name}")
        else:
            item[field_name] = ts
        self.save_json()

    def __edit_due(self):
        selected = self.get_selected_item()
        if not selected:
            return
        self.__edit_timestamp_field(selected, field_name=_DUE_TIMESTAMP)

    def __edit_description(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_item_description(selected)

    def __edit_item_description(self, item: TodoItem):
        new_text = self.call_func_without_curses(
            lambda: edit_text(item["description"], tmp_file_ext=".md")
        )
        if new_text != item["description"]:
            item["description"] = new_text
            self.save_json()
            self.update_screen()

    def __edit_todo_item(self, item: TodoItem):
        _EditTodoItemMenu(
            item,
            on_dict_update=lambda _: self.save_json(),
        ).exec()

    def __new_task(self):
        item = {_STATUS: "none", "description": ""}
        self.__edit_item_description(item)
        if not item["description"]:
            return

        self.items.append(item)
        self.__edit_timestamp_field(item, field_name=_DUE_TIMESTAMP)
        self.__sort_tasks()
        self.save_json()
        self.set_selected_item(item)

    def __reload(self, sort=True):
        if self.load_json():
            self.set_message("reloaded")
        if sort:
            self.__sort_tasks()

    def __sort_tasks(self):
        selected = self.get_selected_item()
        self.items.sort(
            key=lambda item: (
                item.get(_STATUS, "none") == "closed",
                (
                    -item.get(_DUE_TIMESTAMP, 0.0)
                    if item.get(_STATUS, "none") == "closed"
                    else item.get(_DUE_TIMESTAMP, sys.float_info.max)
                ),
                item.get("description"),
            ),
        )
        self.refresh()
        self.set_selected_item(selected)

    def __set_status_wip(self):
        self.__set_selected_item_value({_STATUS: "in_progress"})


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
