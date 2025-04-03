import argparse
import os
from datetime import datetime
from typing import Any, Dict, Optional

from utils.dateutil import parse_datetime
from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputmenu import InputMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


FIELD_CLOSED_TIMESTAMP = "closed_ts"
FIELD_DUE_TIMESTAMP = "due_ts"
FIELD_IMPORTANT = "important"
FIELD_STATUS = "status"

FIELD_DONE_DEPRECATED = "done"
FIELD_DUE_DEPRECATED = "due"

_status_sort_key = {
    "none": 0,
    "in_progress": 1,
    "closed": 2,
}
_status_symbols = {"closed": "[x]", "in_progress": "[=]", "none": "[ ]"}


def _format_timestamp(ts: float, include_year: bool = True) -> str:
    dt = datetime.fromtimestamp(ts)
    date_format = "%Y-%m-%d" if include_year else "%m-%d"
    time_format = "" if (dt.hour == 0 and dt.minute == 0) else " %H:%M"
    return dt.strftime(date_format + time_format)


def get_pretty_ts(ts):
    date_str = ""
    time_diff_str = ""
    date_str = _format_timestamp(ts, include_year=False).ljust(11)

    date = datetime.fromtimestamp(ts)
    if date:
        now = datetime.now(date.tzinfo)
        diff = (date.date() - now.date()).days
        if abs(diff) > 365:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff // 365}y"
        elif abs(diff) > 30:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff // 30}M"
        elif abs(diff) != 0:
            time_diff_str = f"{'+' if diff > 0 else ''}{diff}d"
        elif abs(diff) == 0:
            time_diff_str = "now"
    return f"{time_diff_str:>4} {date_str}"


class _reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        super().__init__(json_file=data_file, backup_json=True)

        self.__sort_tasks()

        self.add_command(self.__duplicate_task, hotkey="ctrl+d")
        self.add_command(self.__edit_description, hotkey="ctrl+e")
        self.add_command(self.__edit_due, hotkey="alt+d")
        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__reload, hotkey="ctrl+r")
        self.add_command(self.__close_task, hotkey="alt+c")
        self.add_command(self.__set_status_wip, hotkey="alt+w")
        self.add_command(self.__set_status_open, hotkey="alt+o")
        self.add_command(self.__toggle_important, hotkey="!")

    def __duplicate_task(self):
        selected = self.get_selected_item()
        if selected:
            copy = selected.copy()
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

    def __toggle_important(self):
        selected = self.get_selected_item()
        if selected:
            if selected.get(FIELD_IMPORTANT):
                self.__set_selected_item_value({FIELD_IMPORTANT: None})
            else:
                self.__set_selected_item_value({FIELD_IMPORTANT: True})

    def get_item_text(self, item: TodoItem) -> str:
        # Date
        if item.get(FIELD_DUE_TIMESTAMP):
            date = get_pretty_ts(item[FIELD_DUE_TIMESTAMP])
        elif item.get(FIELD_CLOSED_TIMESTAMP):
            date = get_pretty_ts(item[FIELD_CLOSED_TIMESTAMP])
        else:
            date = ""

        # Description
        desc_lines = item["description"].splitlines()
        desc = desc_lines[0] + " ..." if len(desc_lines) > 1 else desc_lines[0]

        return (
            _status_symbols[item[FIELD_STATUS]]
            + " "
            + f"{date:<16}"
            + " "
            + ("!! " if item.get(FIELD_IMPORTANT) else "")
            + desc
        )

    def get_item_color(self, item: Any) -> str:
        now = datetime.now()
        if item[FIELD_STATUS] == "in_progress":
            return "green"
        elif item[FIELD_STATUS] == "closed":
            return "blue"

        if item.get(FIELD_IMPORTANT):
            return "yellow"

        due = item.get(FIELD_DUE_TIMESTAMP)
        if due:
            due_date = datetime.fromtimestamp(item[FIELD_DUE_TIMESTAMP])
            if due_date and due_date < now:
                return "red"

        return "white"

    def load_json(self):
        super().load_json()
        for item in self.items:
            if FIELD_DONE_DEPRECATED in item:
                item[FIELD_STATUS] = "closed" if item[FIELD_DONE_DEPRECATED] else "none"
                del item[FIELD_DONE_DEPRECATED]
            if FIELD_DUE_DEPRECATED in item:
                dt = parse_datetime(item[FIELD_DUE_DEPRECATED])
                if dt:
                    item[FIELD_DUE_TIMESTAMP] = dt.timestamp()
                del item[FIELD_DUE_DEPRECATED]

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def save_json(self):
        self.__sort_tasks()
        return super().save_json()

    def __input_date(
        self, prompt: str, default_ts: Optional[float] = None
    ) -> Optional[float]:
        # User inputs a date
        val = InputMenu(
            prompt=prompt,
            text=(_format_timestamp(default_ts) if default_ts is not None else ""),
        ).request_input()
        if not val:
            return None

        # Parse to datetime
        dt = parse_datetime(val)
        if not dt:
            self.set_message("Failed to parse date")
            return None

        # Convert to timestamp
        ts = dt.timestamp()
        return ts

    def __edit_timestamp_field(self, field_name: str):
        # Check selected item
        selected = self.get_selected_item()
        if not selected:
            return

        ts = self.__input_date(
            prompt=field_name,
            default_ts=selected[field_name] if field_name in selected else None,
        )
        if ts is None:
            return

        if ts == selected.get(field_name, 0):
            self.set_message("Skip updating the same date")
            return

        selected[field_name] = ts
        self.save_json()

    def __edit_due(self):
        self.__edit_timestamp_field(field_name=FIELD_DUE_TIMESTAMP)

    def __edit_description(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_item_description(selected)

    def __edit_item_description(self, item: TodoItem):
        new_text = self.call_func_without_curses(lambda: edit_text(item["description"]))
        if new_text != item["description"]:
            item["description"] = new_text
            self.save_json()
            self.update_screen()

    def __edit_todo_item(self, item: TodoItem):
        DictEditMenu(
            item,
            on_dict_update=lambda _: self.save_json(),
        ).exec()

    def __new_task(self):
        item = {FIELD_STATUS: "none", "description": ""}
        self.__edit_item_description(item)
        if item["description"]:
            self.items.append(item)
            self.save_json()
            self.set_selected_item(item)

    def __reload(self):
        self.load_json()
        self.__sort_tasks()
        self.set_message("reloaded")

    def __sort_tasks(self):
        selected = self.get_selected_item()
        self.items.sort(
            key=lambda item: (
                _status_sort_key[item.get(FIELD_STATUS, 0)],
                (
                    _reversor(
                        item.get(
                            FIELD_DUE_TIMESTAMP, item.get(FIELD_CLOSED_TIMESTAMP, 0)
                        )
                    )
                    if item.get(FIELD_STATUS) != "none"
                    else item.get(
                        FIELD_DUE_TIMESTAMP, item.get(FIELD_CLOSED_TIMESTAMP, 0)
                    )
                ),
                item.get("description"),
            ),
        )
        self.set_selected_item(selected)

    def __close_task(self):
        ts = self.__input_date(prompt="close task with date")
        if ts is None:
            return

        self.__set_selected_item_value(
            {
                FIELD_STATUS: "closed",
                FIELD_CLOSED_TIMESTAMP: ts,
            }
        )

    def __set_status_open(self):
        self.__set_selected_item_value({FIELD_STATUS: "none"})

    def __set_status_wip(self):
        self.__set_selected_item_value({FIELD_STATUS: "in_progress"})


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
