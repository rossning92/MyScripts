from typing import Optional

from _shutil import load_json, save_json

from ..menu import Menu


class TextInput(Menu):
    def __init__(self, prompt: str = ">", history_file: Optional[str] = None):
        self.__history_file = history_file
        if self.__history_file:
            self.__history_data = load_json(
                self.__history_file, default={"history": []}
            )
        super().__init__(
            prompt=prompt,
            items=self.__history_data["history"] if self.__history_file else [],
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
                return s
            else:
                return self.get_selected_item()
