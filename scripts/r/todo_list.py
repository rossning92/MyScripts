import argparse
import os
from datetime import datetime
from typing import Any, Dict

from utils.editor import edit_text
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.listeditmenu import ListEditMenu

TodoItem = Dict[str, Any]


class TodoMenu(ListEditMenu[TodoItem]):
    def __init__(
        self,
        data_file: str,
    ):
        super().__init__(json_file=data_file)

        self.items.sort(key=lambda item: item["done"])

        self.add_command(self.__new_task, hotkey="ctrl+n")
        self.add_command(self.__edit_task_description, hotkey="ctrl+e")
        self.add_command(self.__toggle_status, hotkey="ctrl+x")

    def __edit_task_description(self):
        selected = self.get_selected_item()
        if selected:
            new_text = self.call_func_without_curses(
                lambda: edit_text(selected["description"])
            )
            if new_text != selected["description"]:
                selected["description"] = new_text
                self.save_json()

    def __new_task(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        todo_item = {"due": current_date, "done": False, "description": ""}
        self.items.append(todo_item)
        self.__edit_todo_item(todo_item)

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

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__edit_todo_item(selected)

    def get_item_text(self, item: TodoItem) -> str:
        return (
            ("[x] " if item["done"] else "[ ] ")
            + item["due"]
            + " "
            + item["description"]
        )

    def get_item_color(self, item: Any) -> str:
        return "blue" if item["done"] else "white"


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
