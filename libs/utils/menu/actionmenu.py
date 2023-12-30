from typing import Callable, Optional

from _shutil import get_hotkey_abbr

from ..menu import Menu


class _Action:
    def __init__(self, name: str, callback: Callable[[], None]) -> None:
        self.name = name
        self.callback = callback

    def __str__(self):
        return self.name


class ActionMenu(Menu[_Action]):
    def add_action(
        self, func, name: Optional[str] = None, hotkey: Optional[str] = None
    ):
        item_name = name if name else func.__name__
        if hotkey:
            item_name += " (%s)" % (get_hotkey_abbr(hotkey))
        action = _Action(name=item_name, callback=func)
        self.items.append(action)
        self.add_command(
            lambda action=action: self.__on_action(action),
            name=item_name,
            hotkey=hotkey,
        )

    def action(self, name: Optional[str] = None, hotkey: Optional[str] = None):
        def decorator(func):
            nonlocal name
            self.add_action(func, name=name, hotkey=hotkey)
            return func

        return decorator

    def on_enter_pressed(self):
        action = self.get_selected_item()
        if action is not None:
            self.__on_action(action)

    def __on_action(self, action: _Action):
        self.call_func_without_curses(action.callback)
        if self._close_on_selection:
            self.close()
        else:
            self.update_screen()
