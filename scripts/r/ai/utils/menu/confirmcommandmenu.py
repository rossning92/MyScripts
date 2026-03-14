import re

from ai.utils.tools import Settings
from utils.menu.actionmenu import ActionMenu
from utils.menu.confirmmenu import ConfirmMenu


def is_command_trusted(
    command: str, trusted_commands: list[str], ignore_case: bool = False
) -> bool:
    for cmd in trusted_commands:
        pattern = re.escape(cmd).replace(r"\*", ".*")
        flags = re.IGNORECASE if ignore_case else 0
        if re.match(rf"^\s*{pattern}(?:\s+|$)", command, flags=flags):
            return True
    return False


class ConfirmCommandMenu(ConfirmMenu):
    def __init__(self, prompt="", prompt_color="green", **kwargs):
        super().__init__(
            prompt=prompt,
            prompt_color=prompt_color,
            **kwargs
        )
        self.__always = False

    @ActionMenu.action(name="Always", hotkey="a")
    def always_confirm(self):
        self.confirmed = True
        self.__always = True
        self.close()

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
