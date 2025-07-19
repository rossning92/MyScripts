import os

from utils.jsonutil import load_json, save_json

from .dicteditmenu import DictEditMenu


class JsonEditMenu(DictEditMenu):
    def __init__(
        self,
        json_file,
        *,
        default={},
        save_modified_only=True,
        auto_create=True,
        **kwargs,
    ):
        self.__json_file = json_file
        self.__save_modified_only = save_modified_only

        self.data = {
            **self.get_default_values(),
            **(load_json(json_file) if os.path.exists(json_file) else {}),
        }

        if auto_create and not os.path.exists(json_file):
            self.on_dict_update(self.data)

        super().__init__(
            self.data,
            default_dict=default,
            prompt=f"edit {json_file}",
            **kwargs,
        )

    def on_dict_update(self, data):
        default = self.get_default_values()
        save_json(
            self.__json_file,
            (
                {k: v for k, v in data.items() if default[k] != v}
                if self.__save_modified_only
                else {**default, **self.data}
            ),
        )
