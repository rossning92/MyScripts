import argparse
import os
from datetime import datetime
from typing import Any, Dict

from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        super().__init__(json_file=data_file)
        self.add_command(self.__new_task, hotkey="ctrl+n")

    def __new_task(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        todo_item = {"due": current_date, "done": "", "description": ""}
        self.items.append(todo_item)
        self.__edit_todo_item(todo_item)

    def __edit_todo_item(self, item: TodoItem):
        DictEditMenu(
            item,
            on_dict_update=lambda _: self.save_json(),
        ).exec()

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def get_item_text(self, item: TodoItem) -> str:
        return "[ ] " + item["due"] + " " + item["description"]


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
