import re

from ai.utils.tools import Settings
from utils.menu.confirmmenu import confirm
from utils.menu.shellcmdmenu import ShellCmdMenu

TRUSTED_COMMANDS = ["ls", "pwd", "date"]


def bash(command: str) -> str:
    """
    Execute a bash command on the system.
    - Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    - Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    need_confirm = not any(
        re.match(rf"^\s*{re.escape(cmd)}(?:\s+|$)", command) for cmd in TRUSTED_COMMANDS
    )

    if Settings.need_confirm and need_confirm and not confirm(f"Run `{command}`?"):
        raise KeyboardInterrupt("Command execution was canceled by the user")

    menu = ShellCmdMenu(command=command, prompt=f"Running `{command}`")
    menu.exec()
    return menu.get_output()
