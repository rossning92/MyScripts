from typing import List, Optional

from _shutil import load_json, save_json

from ..menu import Menu


class TextInput(Menu):
    def __init__(
        self,
        items: Optional[List[str]] = None,
        prompt: str = ">",
        history_list: Optional[List[str]] = None,
        history_file: Optional[str] = None,
        text="",
    ):
        self.__history_list = history_list
        self.__history_file = history_file
        if self.__history_file:
            self.__history_data = load_json(
                self.__history_file, default={"history": []}
            )
        self.__items = items
        super().__init__(
            prompt=prompt,
            items=self.__items
            if self.__items is not None
            else (self.__history_data["history"] if self.__history_file else []),
            text=text,
        )

    def request_input(self) -> Optional[str]:
        self.exec()
        if self.is_cancelled:
            return None
        else:
            s = self.get_input()
            if s:
                if self.__history_file:
                    if s in self.__history_data["history"]:
                        self.__history_data["history"].remove(s)
                    self.__history_data["history"].insert(0, s)
                    save_json(self.__history_file, self.__history_data)
                if self.__history_list is not None:
                    if s in self.__history_list:
                        self.__history_list.remove(s)
                    self.__history_list.insert(0, s)
                return s
            else:
                return self.get_selected_item()
