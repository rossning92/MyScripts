import argparse
import os
import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, NotRequired, Optional, TypedDict

from utils.dateutil import format_datetime, format_timestamp, parse_datetime
from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.inputdatemenu import input_date
from utils.menu.listeditmenu import ListEditMenu
from utils.textutil import truncate_text


class TodoItem(TypedDict):
    id: int
    description: str
    status: Literal["none", "closed", "in_progress"]
    due_ts: NotRequired[float]


_status_symbols = {"closed": "[x]", "in_progress": "[=]", "none": "[ ]"}


def get_relative_time_str(ts: float) -> str:
    date = datetime.fromtimestamp(ts)
    now = datetime.now(date.tzinfo)
    diff = (date.date() - now.date()).days

    if diff == 0:
        return "today"
    else:
        sign = "+" if diff > 0 else "-"
        days = abs(diff)
        if days > 365:
            years, remainder = divmod(days, 365)
            months = remainder // 30
            return f"{sign}{years}y{f'{months}M' if months else ''}"
        elif days > 30:
            months, days = divmod(days, 30)
            return f"{sign}{months}M{f'{days}d' if days else ''}"
        else:
            return f"{sign}{days}d"


def get_pretty_ts(ts):
    date_str = format_timestamp(ts).ljust(11)
    time_diff_str = get_relative_time_str(ts)
    return f"{time_diff_str:>7} {date_str}"


class _EditTodoItemMenu(DictEditMenu):
    def edit_dict_value(self, data: Dict[str, Any], name: str):
        if name in ("due_ts",):
            ts = input_date(
                prompt=name,
                default_ts=data[name],
            )
            if ts:
                data[name] = ts
        else:
            return super().edit_dict_value(data, name)

    def get_value_str(self, name: str, val: Any) -> str:
        if name in ("due_ts",):
            return format_timestamp(val)
        else:
            return super().get_value_str(name, val)


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        self.__last_tick = 0.0

        super().__init__(prompt="todo", json_file=data_file, backup_json=True)

        self.__sort_tasks()

        self.add_command(self.__duplicate_task, hotkey="ctrl+d")
        self.add_command(self.__edit_description, hotkey="ctrl+e")
        self.add_command(self.__edit_due, hotkey="alt+d")
        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__reload, hotkey="ctrl+r")
        self.add_command(self.__set_status_wip, hotkey="alt+w")
        self.add_command(self.__toggle_status, hotkey="alt+x")

    def __new_task(self):
        self.__add_task_interactive(
            {
                "id": self.get_next_id(),
                "status": "none",
                "description": "",
            }
        )

    def __duplicate_task(self):
        selected = self.get_selected_item()
        if selected:
            item = selected.copy()
            item["status"] = "none"
            self.__add_task_interactive(item)

    def __add_task_interactive(self, item: TodoItem):
        self.__edit_item_description(item)
        if not item["description"]:
            return
        self.__edit_timestamp_field(item)
        self.__add_item(item)

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
            status = "closed" if selected.get("status") != "closed" else "none"
            self.__set_selected_item_value({"status": status})

    def get_item_text(self, item: TodoItem) -> str:
        # Date
        ts = item.get("due_ts")
        date = get_pretty_ts(ts) if ts else ""

        # Description
        desc = truncate_text(item["description"], max_lines=1)

        return f"{_status_symbols[item['status']]} {date:<19} {desc}"

    def get_item_color(self, item: Any) -> str:
        status = item["status"]
        if status == "in_progress":
            return "green"
        if status == "closed":
            return "blue"

        due = item.get("due_ts")
        if due and datetime.fromtimestamp(due) < datetime.now():
            return "red"

        return "white"

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def on_idle(self):
        now = time.time()
        if now > self.__last_tick + 1.0:
            self.__last_tick = now
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
            if super().load_json():
                self.__ensure_ids()
                return True
            return False
        except Exception as e:
            self.set_message(f"Error on loading: {e}")
            return False

    def __ensure_ids(self):
        for item in self.items:
            if "id" not in item:
                item["id"] = self.get_next_id()

    def get_next_id(self) -> int:
        return max((item.get("id", 0) for item in self.items), default=0) + 1

    def __add_item(self, item: TodoItem):
        self.items.append(item)
        self.__sort_tasks()
        self.save_json()
        self.set_selected_item(item)

    def open_ai_agent(self, system_prompt: Optional[str] = None):
        system_prompt = (
            "You can use `run_script r/todo_list.py` CLI tool to manage your todo list and tasks. You must run `run_script r/todo_list.py --help` to learn how to use the tool first."
        )
        super().open_ai_agent(system_prompt=system_prompt)

    def __edit_timestamp_field(self, item: TodoItem):
        ts = input_date(prompt="date", default_ts=item.get("due_ts"))
        if ts is None:
            return

        if ts == item.get("due_ts"):
            self.set_message("Skip updating the same date")
            return

        if ts <= 0.0:
            item.pop("due_ts", None)
            self.set_message("Reset date")
        else:
            item["due_ts"] = ts
        self.save_json()

    def __edit_due(self):
        selected = self.get_selected_item()
        if not selected:
            return
        self.__edit_timestamp_field(selected)

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

    def __reload(self, sort=True):
        if self.load_json():
            self.set_message("reloaded")
        if sort:
            self.__sort_tasks()

    def __sort_tasks(self):
        selected = self.get_selected_item()
        self.items.sort(
            key=lambda item: (
                item.get("status", "none") == "closed",
                (
                    -item.get("due_ts", 0.0)
                    if item.get("status", "none") == "closed"
                    else item.get("due_ts", sys.float_info.max)
                ),
                item.get("description"),
            ),
        )
        self.refresh()
        self.set_selected_item(selected)

    def __set_status_wip(self):
        self.__set_selected_item_value({"status": "in_progress"})


def _main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--data-file",
        type=str,
        help="Path to todo list data file",
        default=os.environ.get("TODO_DATA_FILE"),
    )

    subparsers = parser.add_subparsers(dest="command")

    # Command: add
    add_parser = subparsers.add_parser("add", help="Add a new todo item")
    add_parser.add_argument(
        "--desc", required=True, help="Description of the todo item"
    )
    add_parser.add_argument("--due", help="Due date/time")

    # Command: delete
    delete_parser = subparsers.add_parser("delete", help="Delete a todo item")
    delete_parser.add_argument("id", type=int, help="ID of the todo item to delete")

    # Command: edit
    edit_parser = subparsers.add_parser("edit", help="Edit an existing todo item")
    edit_parser.add_argument("id", type=int, help="ID of the todo item to edit")
    edit_parser.add_argument("--desc", help="New description for the todo item")
    edit_parser.add_argument("--due", help="New due date/time")
    edit_parser.add_argument(
        "--status", choices=["none", "closed", "in_progress"], help="New status"
    )

    # Command: list
    list_parser = subparsers.add_parser("list", help="List todo items")
    list_parser.add_argument(
        "--all", action="store_true", help="Show all items including closed ones"
    )

    args = parser.parse_args()

    if args.command == "add":
        menu = TodoMenu(data_file=args.data_file)
        item: TodoItem = {
            "id": menu.get_next_id(),
            "description": args.desc,
            "status": "none",
        }
        if args.due:
            dt = parse_datetime(args.due)
            if dt:
                item["due_ts"] = dt.timestamp()
            else:
                print(f"Error: Invalid date format: {args.due}")
                sys.exit(1)
        menu.items.append(item)
        menu.save_json()
        print(f"Todo item added (id={item['id']})")
    elif args.command == "delete":
        menu = TodoMenu(data_file=args.data_file)
        item_to_delete = next(
            (item for item in menu.items if item.get("id") == args.id), None
        )
        if item_to_delete:
            menu.items.remove(item_to_delete)
            menu.save_json()
            print(f"Todo item deleted (id={args.id})")
        else:
            print(f"Todo item not found (id={args.id})")
            sys.exit(1)
    elif args.command == "edit":
        menu = TodoMenu(data_file=args.data_file)
        item = next((item for item in menu.items if item.get("id") == args.id), None)
        if not item:
            print(f"Todo item not found (id={args.id})")
            sys.exit(1)

        if args.desc is not None:
            item["description"] = args.desc
        if args.status is not None:
            item["status"] = args.status
        if args.due is not None:
            dt = parse_datetime(args.due)
            if dt:
                item["due_ts"] = dt.timestamp()
            else:
                print(f"Error: Invalid date format: {args.due}")
                sys.exit(1)

        menu.save_json()
        print(f"Todo item updated (id={args.id})")
    elif args.command == "list":
        menu = TodoMenu(data_file=args.data_file)
        filtered_items = [
            item for item in menu.items if args.all or item.get("status") != "closed"
        ]
        for i, item in enumerate(filtered_items):
            if i > 0:
                print("---")
            print(f"ID: {item.get('id', 0)}")
            print(f"Status: {item.get('status', 'none')}")

            ts = item.get("due_ts")
            if ts:
                date_str = format_timestamp(ts, show_year=True)
                print(f"Due: {date_str}")
            else:
                print("Due: None")

            print(f"Description: {item.get('description', '')}")
    else:
        menu = TodoMenu(data_file=args.data_file)
        menu.exec()


if __name__ == "__main__":
    _main()
