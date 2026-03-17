import json
import re

from ai.utils.tools import Settings
from utils.menu.confirmmenu import ConfirmMenu


def is_command_allowed(
    command: str,
    allowed_commands: list[str],
    ignore_case: bool = False,
) -> bool:
    flags = re.IGNORECASE if ignore_case else 0
    for cmd in allowed_commands:
        pattern = re.escape(cmd).replace(r"\*", ".*")
        if re.match(rf"^\s*{pattern}(?:\s+|$)", command, flags=flags):
            return True
    return False


class ConfirmCommandMenu(ConfirmMenu):
    def __init__(self, command: str, **kwargs):
        self.command_base = command.split()[0] if command.strip() else ""
        super().__init__(**kwargs)
        self.__always = False
        self.__save = False

        if self.command_base:
            self.add_action(
                f"allow all `{self.command_base} *`",
                self.__always_confirm,
                hotkey="a",
            )
            self.add_action(
                f"allow all `{self.command_base} *` (save to config)",
                self.__save_and_confirm,
                hotkey="s",
            )

    def __always_confirm(self):
        self.confirmed = True
        self.__always = True
        self.close()

    def __save_and_confirm(self):
        self.confirmed = True
        self.__always = True
        self.__save = True
        self.close()

    @staticmethod
    def confirm_command(
        command: str,
        allowed_commands: list[str],
        save_path: str,
        ignore_case: bool = False,
        prompt_prefix: str = "Run",
    ):
        if not Settings.need_confirm:
            return

        if is_command_allowed(command, allowed_commands, ignore_case):
            return

        menu = ConfirmCommandMenu(
            command=command, prompt=f"{prompt_prefix} `{command}`?"
        )
        menu.exec()
        if not menu.is_confirmed():
            raise KeyboardInterrupt("Command execution was canceled by the user")

        if menu.__always:
            if menu.command_base not in allowed_commands:
                allowed_commands.append(menu.command_base)
                allowed_commands.sort()

            if menu.__save and save_path:
                with open(save_path, "w") as f:
                    json.dump(allowed_commands, f, indent=4)
