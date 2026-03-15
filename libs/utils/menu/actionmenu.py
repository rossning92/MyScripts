from typing import Callable, Optional, Union

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
            return "[%s] %s" % (get_hotkey_abbr(self.hotkey), self.name)
        else:
            return self.name


class ActionMenu(Menu[_Action]):
    def __init__(self, **kwags):
        super().__init__(**kwags)
        for cls in reversed(self.__class__.__mro__):
            for name, attr in cls.__dict__.items():
                if hasattr(attr, "_action_info"):
                    for info in getattr(attr, "_action_info"):
                        self.add_action(
                            name=info["name"] if info["name"] else name,
                            callback=getattr(self, name),
                            hotkey=info["hotkey"],
                        )

    @staticmethod
    def action(
        name_or_func: Optional[Union[str, Callable]] = None,
        hotkey: Optional[str] = None,
        **kwargs,
    ):
        if "name" in kwargs:
            name = kwargs["name"]
        elif isinstance(name_or_func, str):
            name = name_or_func
        else:
            name = None

        if "k" in kwargs:
            hotkey = kwargs["k"]

        def decorator(method):
            if not hasattr(method, "_action_info"):
                setattr(method, "_action_info", [])
            getattr(method, "_action_info").append({"name": name, "hotkey": hotkey})
            return method

        if callable(name_or_func):
            return decorator(name_or_func)
        else:
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


action = ActionMenu.action
