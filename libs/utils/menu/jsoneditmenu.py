import os

from utils.jsonutil import load_json, save_json

from .dicteditmenu import DictEditMenu


class JsonEditMenu(DictEditMenu):
    def __init__(self, json_file, *, default={}):
        data = load_json(json_file) if os.path.exists(json_file) else {}
        self.data = {**default, **data}

        def on_dict_update(dict):
            self.data = {k: v for k, v in dict.items() if default[k] != v}
            save_json(
                json_file,
                self.data,
            )

        super().__init__(
            self.data,
            default_dict=default,
            on_dict_update=on_dict_update,
            prompt=f"edit {json_file}",
        )
