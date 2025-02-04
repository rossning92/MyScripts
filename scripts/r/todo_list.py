import argparse
import os
from typing import Any, Dict

from utils.jsonutil import load_json, save_json
from utils.menu import Menu
from utils.menu.dicteditmenu import DictEditMenu


class TodoMenu(Menu[Dict[str, Any]]):
    def __init__(
        self,
        data_file: str,
    ):
        self.__load_data(data_file)
        super().__init__(items=self.__items)

    def __load_data(self, data_file):
        self.__data_file = data_file
        self.__items = load_json(self.__data_file, default=[])

    def __save_data(self):
        save_json(self.__data_file, data=self.__items)

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            DictEditMenu(
                selected,
                on_dict_update=lambda _: self.__save_data(),
            ).exec()

    def get_item_text(self, item: Dict[str, Any]) -> str:
        return item["due"] + " " + item["description"]


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
