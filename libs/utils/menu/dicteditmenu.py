import curses
import curses.ascii
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from utils.clip import get_clip, set_clip
from utils.editor import edit_text

from . import Menu
from .inputmenu import InputMenu


class _DictValueEditMenu(InputMenu):
    def __init__(
        self,
        dict_: Dict,
        name: str,
        type: Type,
        dict_history_values: List,
        items: List,
    ):
        self.__dict = dict_
        self.__dict_history_values = dict_history_values
        self.__name = name
        self.__type = type

        super().__init__(
            items=items,
            prompt=name,
            text=self.__dict[self.__name],
        )

    def on_enter_pressed(self):
        text = self.get_text()
        assert text is not None

        val: Union[str, int, float, bool]
        if self.__type == str:
            val = text.strip()
        elif self.__type == int:
            val = int(text)
        elif self.__type == float:
            val = float(text)
        elif self.__type == bool or self.__type == type(None):
            if text.lower() == "true":
                val = True
            elif text.lower() == "false":
                val = False
            elif text == "1":
                val = True
            elif text == "0":
                val = False
            else:
                raise Exception("Invalid bool value: {}".format(text))
        else:
            raise Exception("Invalid type: {}".format(self.__type))

        self.__dict[self.__name] = val

        # Save edit history
        if val in self.__dict_history_values:  # avoid duplicates
            self.__dict_history_values.remove(val)
        self.__dict_history_values.insert(0, val)

        self.close()

    def on_char(self, ch):
        if ch == "\t":
            val = self.get_selected_item()
            if val is not None:
                self.set_input(val)
            return True
        elif ch == curses.KEY_DC:  # delete key
            i = self.get_selected_index()
            del self.__dict_history_values[i]
            return True

        return False


class _KeyValuePair:
    def __init__(
        self,
        dict: Dict[str, Any],
        key: str,
        key_display_width: int,
        default_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.key = key

        self.__default_dict = default_dict
        self.__dict = dict
        self.__key_display_width = key_display_width

    def __str__(self) -> str:
        value = self.__dict[self.key]
        modified = (
            self.__default_dict is not None
            and value != self.__default_dict[self.key]
        )
        return "{}:{}{}{}".format(
            self.key.ljust(self.__key_display_width),
            "\n" if isinstance(value, str) and "\n" in value else " ",
            value,
            " (*)" if modified else "",
        )


class DictEditMenu(Menu[_KeyValuePair]):
    def __init__(
        self,
        dict_,
        default_dict: Optional[Dict[str, Any]] = None,
        on_dict_update: Optional[Callable[[Dict], None]] = None,
        dict_history: Dict[str, List[Any]] = {},
        on_dict_history_update: Optional[Callable[[Dict[str, List[Any]]], None]] = None,
        prompt="",
    ):
        super().__init__(
            prompt=prompt,
            highlight=OrderedDict([(r"\(\*\)", "green")]),
            wrap_text=True,
        )
        self.dict_ = dict_
        self.default_dict = default_dict
        self.on_dict_update = on_dict_update
        self.label = prompt
        self.dict_history = dict_history
        self.on_dict_history_update = on_dict_history_update

        self.__init_items()

        self.add_command(self.__copy_selected_dict_value, hotkey="ctrl+y")
        self.add_command(self.__prev_value, hotkey="left")
        self.add_command(self.__next_value, hotkey="right")
        self.add_command(self.__paste_value, hotkey="ctrl+v")
        self.add_command(self.__edit_value, hotkey="ctrl+e")

    def __prev_value(self):
        self.__prev_or_next_value(prev=True)

    def __next_value(self):
        self.__prev_or_next_value(prev=False)

    def __prev_or_next_value(self, prev=False):
        key = self.get_selected_key()
        if key is not None:
            value = self.dict_[key]
            if isinstance(value, bool):
                self.dict_[key] = not self.dict_[key]
                self.__notify_dict_updated()
                self.update_screen()
            elif isinstance(value, str):
                if self.dict_history and key in self.dict_history:
                    values = self.dict_history[key]
                    try:
                        index = values.index(value)
                        index = (
                            min(index + 1, len(values) - 1)
                            if prev
                            else max(0, index - 1)
                        )
                        self.dict_[key] = values[index]
                        self.__notify_dict_updated()
                    except ValueError:
                        pass

    def __edit_value(self):
        key = self.get_selected_key()
        if key is not None:
            value = self.dict_[key]
            if isinstance(value, str):
                new_value = self.call_func_without_curses(lambda: edit_text(value))
                if new_value != value:
                    self.set_dict_value(key, new_value)

    def __paste_value(self):
        key = self.get_selected_key()
        if key is not None:
            value = self.dict_[key]
            if isinstance(value, str):
                val = get_clip()
                self.set_dict_value(key, val)

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
        self.update_screen()

    def __init_items(self):
        if len(self.dict_) == 0:
            return

        # Get max width for keys
        keys = list(self.dict_.keys())
        max_width = max([len(x) for x in keys]) + 1

        kvps: List[Tuple[str, bool]] = []
        for key in keys:
            modified = (
                self.default_dict is not None
                and self.dict_[key] != self.default_dict[key]
            )
            kvps.append((key, modified))

        # Show modified values first
        kvps = sorted(kvps, key=lambda x: x[1], reverse=True)

        # Update items
        self.items.clear()
        for key, _ in kvps:
            self.items.append(
                _KeyValuePair(
                    self.dict_,
                    key=key,
                    key_display_width=max_width,
                    default_dict=self.default_dict,
                )
            )

    def on_enter_pressed(self):
        self.__edit_dict_value()

    def get_selected_key(self) -> Optional[str]:
        selected = self.get_selected_item()
        if selected is not None:
            return selected.key
        else:
            return None

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
        self.update_screen()

    def set_dict_value(self, name: str, value: str):
        # Update dict
        self.dict_[name] = value

        # Update dict history
        dict_history_values = self.__get_dict_history_values(name)
        if value in dict_history_values:  # avoid duplicates
            dict_history_values.remove(value)
        dict_history_values.insert(0, value)

        self.__notify_dict_updated()
        self.update_screen()

    def get_value(self, name: str):
        return self.dict_[name]
