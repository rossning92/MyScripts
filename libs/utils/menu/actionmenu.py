from collections import defaultdict
from functools import partial
from typing import Callable, DefaultDict, List, Optional

from _shutil import get_hotkey_abbr

from .menu import Menu


class _Action:
    def __init__(
        self, name: str, callback: Callable, hotkey: Optional[str] = None
    ) -> None:
        self.name = name
        self.callback = callback
        self.hotkey = hotkey

    def __str__(self):
        if self.hotkey:
            return "%s (%s)" % (self.name, get_hotkey_abbr(self.hotkey))
        else:
            return self.name


class ActionMenu(Menu[_Action]):
    __class_actions: DefaultDict[str, List[_Action]] = defaultdict(list)

    def __init__(self, **kwags):
        super().__init__(**kwags)
        class_name = self.__class__.__name__
        for act in ActionMenu.__class_actions[class_name]:
            self.__add_action(
                _Action(
                    name=act.name,
                    callback=partial(act.callback, self),
                    hotkey=act.hotkey,
                )
            )

    @staticmethod
    def action(name: Optional[str] = None, hotkey: Optional[str] = None):
        def decorator(method):
            class_name = method.__qualname__.split(".")[0]
            action = _Action(
                name=name if name else method.__name__, callback=method, hotkey=hotkey
            )
            ActionMenu.__class_actions[class_name].append(action)
            return method

        return decorator

    def func(self, name: Optional[str] = None, hotkey: Optional[str] = None):
        def decorator(func):
            self.__add_action(
                _Action(
                    name=name if name else func.__name__, callback=func, hotkey=hotkey
                )
            )
            return func

        return decorator

    def on_enter_pressed(self):
        action = self.get_selected_item()
        if action is not None:
            self.__on_action(action)

    def __add_action(self, action: _Action):
        self.items.append(action)
        self.add_command(
            lambda action=action: self.__on_action(action),
            name=action.name,
            hotkey=action.hotkey,
        )

    def add_action(self, name: str, callback: Callable, hotkey: Optional[str] = None):
        action = _Action(name=name, callback=callback, hotkey=hotkey)
        self.__add_action(action)

    def __on_action(self, action: _Action):
        self.run_raw(action.callback)
        if self.close_on_selection:
            self.close()
        else:
            self.update_screen()
