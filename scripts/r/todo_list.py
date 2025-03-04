import argparse
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputmenu import InputMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


FIELD_CLOSED_TS = "closed_ts"
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


def _format_timestamp(ts: int) -> str:
    date = datetime.fromtimestamp(ts)
    if date:
        if date.hour == 0 and date.minute == 0:
            return date.strftime("%m-%d")
        else:
            return date.strftime("%m-%d %H:%M")
    else:
        return ""


def _parse_date(text: str) -> Optional[datetime]:
    pattern = (
        r"(?:(?P<year>\d{2,4})-)?(?P<month>\d{1,2})-(?P<day>\d{1,2})"
        r"(\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?"
    )
    match = re.search(pattern, text)
    if match:
        year = int(match.group("year") or datetime.now().year)
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        return datetime(year, month, day, hour, minute)
    else:
        return None


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
        self.add_command(self.__set_status_closed, hotkey="alt+x")
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
        date_str = ""
        time_diff_str = ""
        if item.get(FIELD_DUE_TIMESTAMP):
            ts = item[FIELD_DUE_TIMESTAMP]
            date_str = _format_timestamp(ts).ljust(11)

            date = datetime.fromtimestamp(ts)
            if date:
                now = datetime.now(date.tzinfo)
                diff = (date - now).days
                if abs(diff) > 365:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff // 365}yr"
                elif abs(diff) > 30:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff // 30}mo"
                elif abs(diff) != 0:
                    time_diff_str = f"{'+' if diff > 0 else ''}{diff}d"

        return (
            _status_symbols[item[FIELD_STATUS]]
            + (" ! " if item.get(FIELD_IMPORTANT) else "   ")
            + " "
            + f"{time_diff_str:>5} {date_str:<11}"
            + " "
            + item["description"]
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
                dt = _parse_date(item[FIELD_DUE_DEPRECATED])
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

    def __edit_due(self):
        # Check selected item
        selected = self.get_selected_item()
        if not selected:
            return

        # User inputs a date
        val = InputMenu(
            prompt="due date",
            text=(
                _format_timestamp(selected[FIELD_DUE_TIMESTAMP])
                if FIELD_DUE_TIMESTAMP in selected
                else ""
            ),
        ).request_input()
        if not val:
            return

        # Parse to datetime
        dt = _parse_date(val)
        if not dt:
            self.set_message("Failed to parse date")
            return

        # Convert to timestamp
        ts = dt.timestamp()
        if ts == selected.get(FIELD_DUE_TIMESTAMP, 0):
            self.set_message("Skip updating the same date")
            return

        selected[FIELD_DUE_TIMESTAMP] = ts
        self.save_json()

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
                _reversor(item.get(FIELD_DUE_TIMESTAMP, 0)),
                item.get("description"),
            ),
        )
        self.set_selected_item(selected)

    def __set_status_closed(self):
        self.__set_selected_item_value(
            {
                FIELD_STATUS: "closed",
                FIELD_CLOSED_TS: datetime.now().timestamp(),
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
