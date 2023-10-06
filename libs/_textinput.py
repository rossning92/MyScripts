from typing import Optional

from _menu import Menu
from _shutil import load_json, save_json


class TextInput(Menu):
    def __init__(self, history_file: Optional[str] = None):
        self.__history_file = history_file
        if self.__history_file:
            self.__history_data = load_json(
                self.__history_file, default={"adhocPromptHistory": []}
            )
        super().__init__(label=">", items=self.__history_data["adhocPromptHistory"])

    def request_input(self) -> Optional[str]:
        self.exec()
        if self.is_cancelled:
            return None
        else:
            s = self.get_input()
            if s:
                if s in self.__history_data["adhocPromptHistory"]:
                    self.__history_data["adhocPromptHistory"].remove(s)
                self.__history_data["adhocPromptHistory"].insert(0, s)
                if self.__history_file:
                    save_json(self.__history_file, self.__history_data)
                return s
            else:
                return self.get_selected_item()
