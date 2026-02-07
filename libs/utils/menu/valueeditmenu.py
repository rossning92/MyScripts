from typing import (
    Any,
    List,
    Optional,
    Union,
)

from utils.jsonschema import JSONSchema

from .menu import Menu


class ValueEditMenu(Menu[str]):
    def __init__(
        self,
        type: JSONSchema,
        dict_history_values: Optional[List] = None,
        items: Optional[List] = None,
        value: Optional[Any] = None,
        prompt="",
    ):
        self.value = value

        self.__dict_history_values = dict_history_values
        self.__type = type

        if self.__type["type"] == "string" and "enum" in self.__type:
            items = self.__type["enum"].copy()

        super().__init__(
            items=items,
            prompt=prompt,
        )

        self.add_command(self.__delete_history_value, hotkey="delete")

    def on_enter_pressed(self):
        text = self.get_text()
        assert text is not None

        val: Union[str, int, float, bool]
        if self.__type["type"] == "string":
            if "enum" in self.__type:
                selected_val = self.get_selected_item()
                assert selected_val
                val = selected_val
            else:
                val = text.strip()
        elif self.__type["type"] == "integer":
            val = int(text)
        elif self.__type["type"] == "number":
            val = float(text)
        elif self.__type["type"] == "boolean":
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

        self.value = val

        # Save edit history
        if self.__dict_history_values is not None:
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
        return False

    def __delete_history_value(self):
        if self.__dict_history_values is not None:
            i = self.get_selected_index()
            if i >= 0:
                del self.__dict_history_values[i]
