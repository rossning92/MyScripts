import os
import sys

from _script import get_default_script_config_file, get_script_default_config
from _shutil import load_yaml, save_yaml
from _term import Menu


class DictValueEditWindow(Menu):
    def __init__(self, stdscr, dict_, name, type, default_vals=[]):
        self.dict_ = dict_
        self.name = name
        self.type = type

        super().__init__(
            items=default_vals,
            stdscr=stdscr,
            label=name + ":",
            text="",
        )

    def on_enter_pressed(self):
        val = self.get_text()
        if self.type == str:
            val = val.strip()
        elif self.type == int:
            val = int(val)
        elif self.type == float:
            val = float(val)
        elif self.type == bool:
            if val == "true":
                val = True
            elif val == "false":
                val = False
            elif val == "1":
                val = True
            elif val == "0":
                val = False
            else:
                raise Exception("Unknown bool value: {}".format(val))
        else:
            raise Exception("Unknown type: {}".format(self.type))

        self.dict_[self.name] = val

        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_text()
            if val is not None:
                self.input_.set_text(val)
            return True

        return False


class DictEditWindow(Menu):
    def __init__(self, dict_):
        super().__init__()
        self.dict_ = dict_
        self.enter_pressed = False
        self.update_items()

    def update_items(self):
        self.items.clear()

        keys = list(self.dict_.keys())
        max_width = max([len(x) for x in keys]) + 1
        for key in keys:
            self.items.append("{}: {}".format(key.ljust(max_width), self.dict_[key]))

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            self.edit_dict_value()
            return True
        return False

    def edit_dict_value(self):
        index = self.get_selected_index()
        name = list(self.dict_.keys())[index]
        DictValueEditWindow(
            self.stdscr,
            self.dict_,
            name,
            type(self.dict_[name]),
        ).exec()
        self.update_items()
        self.input_.clear()


if __name__ == "__main__":
    default_config = get_script_default_config()

    script_path = os.environ["_SCRIPT"]
    script_config_file = get_default_script_config_file(script_path)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    w = DictEditWindow(data)
    ret = w.exec()

    if ret == -1:
        sys.exit(0)

    data = {k: v for k, v in data.items() if default_config[k] != v}

    save_yaml(data, script_config_file)
