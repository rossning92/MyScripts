import curses
import curses.ascii
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

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
            label=name,
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
        label="",
    ):
        super().__init__(label=label)
        self.dict_ = dict_
        self.default_dict = default_dict
        self.enter_pressed = False
        self.on_dict_update = on_dict_update
        self.label = label
        self.dict_history = dict_history
        self.on_dict_history_update = on_dict_history_update

        self.update_items()

    def update_items(self):
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
            self.edit_dict_value()
            return True
        return False

    def edit_dict_value(self):
        index = self.get_selected_index()
        name = list(self.dict_.keys())[index]
        val = self.dict_[name]

        if name not in self.dict_history:
            dict_history_values = self.dict_history[name] = []
        else:
            dict_history_values = self.dict_history[name]

        _DictValueEditMenu(
            dict_=self.dict_,
            name=name,
            type=type(val),
            items=dict_history_values,
            dict_history_values=dict_history_values,
        ).exec()

        if self.on_dict_update:
            self.on_dict_update(self.dict_)
        if self.on_dict_history_update:
            self.on_dict_history_update(self.dict_history)

        self.update_items()
        self._input.clear()
