from typing import Generic, List, Optional, TypeVar

from utils.jsonschema import JSONSchema
from utils.jsonutil import try_load_json, try_save_json
from utils.menu import Menu
from utils.menu.confirmmenu import ConfirmMenu

T = TypeVar("T")


class ListEditMenu(Menu, Generic[T]):
    def __init__(
        self,
        items: Optional[List[T]] = None,
        json_file: Optional[str] = None,
        backup_json=False,
        item_type: Optional[JSONSchema] = None,
        **kwargs
    ):
        self.__backup_json = backup_json
        self.__json_file = json_file
        self.__last_mtime = 0.0
        self.__item_type = item_type

        super().__init__(items=items if items is not None else [], **kwargs)

        self.load_json()

        self.add_command(self.delete_selected_item, hotkey="ctrl+k")
        self.add_command(self.__add_item, hotkey="ctrl+n")

    def __add_item(self):
        pass

    def load_json(self) -> bool:
        if self.__json_file is not None:
            result = try_load_json(
                self.__json_file, default=[], last_mtime=self.__last_mtime
            )
            if result is not None:
                self.items[:], self.__last_mtime = result
                if not isinstance(self.items[:], list):
                    raise TypeError("JSON data must be a list")
                return True
        return False

    def delete_selected_item(self):
        index = self.get_selected_index()
        if 0 <= index < len(self.items):
            confirm_menu = ConfirmMenu(prompt="delete item?")
            confirm_menu.exec()
            if confirm_menu.is_confirmed():
                del self.items[index]
                self.update_screen()
                self.save_json()

    def append_item(self, item: T):
        self.items.append(item)
        self.update_screen()
        self.save_json()

    def clear(self):
        self.items.clear()
        self.update_screen()
        self.save_json()

    def save_json(self):
        if self.__json_file:
            self.__last_mtime = try_save_json(
                self.__json_file,
                self.items,
                last_mtime=self.__last_mtime,
                backup=self.__backup_json,
            )
