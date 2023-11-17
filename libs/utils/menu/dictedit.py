import curses
import curses.ascii
from typing import Any, Callable, Dict, List, Optional

from _shutil import set_clip

from ..menu import Menu


class _DictValueEditMenu(Menu):
    def __init__(
        self,
        dict_,
        name,
        type,
        dict_history_values: List,
        items: List,
    ):
        self.dict_ = dict_
        self.dict_history_values = dict_history_values
        self.name = name
        self.type = type

        super().__init__(
            items=items,
            prompt=name,
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
        elif self.type == bool or self.type == type(None):
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
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

        # Save edit history
        if val in self.dict_history_values:  # avoid duplicates
            self.dict_history_values.remove(val)
        self.dict_history_values.insert(0, val)

        self.close()

    def on_char(self, ch):
        if ch == "\t":
            val = self.get_selected_item()
            if val is not None:
                self.set_input(val)
            return True
        elif ch == curses.KEY_DC:  # delete key
            i = self.get_selected_index()
            del self.dict_history_values[i]
            return True

        return False


class DictEditMenu(Menu):
    def __init__(
        self,
        dict_,
        default_dict=None,
        on_dict_update: Optional[Callable[[Dict], None]] = None,
        dict_history: Dict[str, List[Any]] = {},
        on_dict_history_update: Optional[Callable[[Dict[str, List[Any]]], None]] = None,
        prompt="",
    ):
        super().__init__(prompt=prompt)
        self.dict_ = dict_
        self.default_dict = default_dict
        self.enter_pressed = False
        self.on_dict_update = on_dict_update
        self.label = prompt
        self.dict_history = dict_history
        self.on_dict_history_update = on_dict_history_update

        self.__update_items()

        self.add_command(self.__copy_selected_dict_value, hotkey="ctrl+y")
        self.add_command(self.__toggle_value, hotkey="left")
        self.add_command(self.__toggle_value, hotkey="right")

    def __toggle_value(self):
        key = self.get_selected_key()
        if key is not None:
            value = self.dict_[key]
            value_type = type(value)
            if value_type == bool:
                self.dict_[key] = not self.dict_[key]
                self.__notify_dict_updated()
                self.__update_items()

    def __copy_selected_dict_value(self):
        key = self.get_selected_key()
        if key is not None:
            value = self.dict_[key]
            set_clip(value)
            self.set_message(f"copied: {value}")

    def __notify_dict_updated(self):
        if self.on_dict_update:
            self.on_dict_update(self.dict_)
        if self.on_dict_history_update:
            self.on_dict_history_update(self.dict_history)

    def __update_items(self):
        if len(self.dict_) == 0:
            return

        self.items.clear()

        keys = list(self.dict_.keys())
        max_width = max([len(x) for x in keys]) + 1
        for key in keys:
            s = "{}: {}".format(key.ljust(max_width), self.dict_[key])
            if self.default_dict is not None:
                if self.dict_[key] != self.default_dict[key]:
                    s += " (*)"
            self.items.append(s)

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == "\t":
            self.__edit_dict_value()
            return True
        else:
            return super().on_char(ch)

    def get_selected_key(self) -> Optional[str]:
        index = self.get_selected_index()
        if index < 0:
            return None
        else:
            return list(self.dict_.keys())[index]

    def __get_dict_history_values(self, name: str) -> List[str]:
        if name not in self.dict_history:
            dict_history_values = self.dict_history[name] = []
        else:
            dict_history_values = self.dict_history[name]
        return dict_history_values

    def __edit_dict_value(self):
        name = self.get_selected_key()
        if name is None:
            return

        val = self.dict_[name]

        dict_history_values = self.__get_dict_history_values(name)
        _DictValueEditMenu(
            dict_=self.dict_,
            name=name,
            type=type(val),
            items=dict_history_values,
            dict_history_values=dict_history_values,
        ).exec()

        self.__notify_dict_updated()
        self.__update_items()

    def set_dict_value(self, name: str, value: str):
        # Update dict
        self.dict_[name] = value

        # Update dict history
        dict_history_values = self.__get_dict_history_values(name)
        if value in dict_history_values:  # avoid duplicates
            dict_history_values.remove(value)
        dict_history_values.insert(0, value)

        self.__notify_dict_updated()
        self.__update_items()
