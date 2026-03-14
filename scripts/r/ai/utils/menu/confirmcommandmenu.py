import re

from ai.utils.tools import Settings
from utils.menu.menu import Menu


def is_command_trusted(
    command: str, trusted_commands: list[str], ignore_case: bool = False
) -> bool:
    for cmd in trusted_commands:
        pattern = re.escape(cmd).replace(r"\*", ".*")
        flags = re.IGNORECASE if ignore_case else 0
        if re.match(rf"^\s*{pattern}(?:\s+|$)", command, flags=flags):
            return True
    return False


class ConfirmCommandMenu(Menu):
    def __init__(self, prompt="", prompt_color="green", **kwargs):
        super().__init__(
            prompt=prompt + " (y/n/a)",
            prompt_color=prompt_color,
            search_mode=False,
            **kwargs
        )
        self.__confirmed = False
        self.__always = False
        self.add_command(self.__confirm, hotkey="y")
        self.add_command(self.__cancel, hotkey="n")
        self.add_command(self.__always_confirm, hotkey="a")

    def __confirm(self):
        self.__confirmed = True
        self.close()

    def __cancel(self):
        self.__confirmed = False
        self.close()

    def __always_confirm(self):
        self.__confirmed = True
        self.__always = True
        self.close()

    def on_enter_pressed(self):
        self.__confirm()

    def is_confirmed(self):
        return self.__confirmed

    def is_always(self):
        return self.__always

    @staticmethod
    def confirm_command(
        command: str,
        trusted_commands: list[str],
        ignore_case: bool = False,
        prompt_prefix: str = "Run",
    ):
        if not Settings.need_confirm:
            return

        if is_command_trusted(command, trusted_commands, ignore_case):
            return

        menu = ConfirmCommandMenu(f"{prompt_prefix} `{command}`?")
        menu.exec()
        if not menu.is_confirmed():
            raise KeyboardInterrupt("Command execution was canceled by the user")
        if menu.is_always():
            trusted_commands.append(command.split()[0])
