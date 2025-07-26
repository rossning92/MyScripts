from ai.tools import Settings
from utils.menu.confirmmenu import confirm
from utils.menu.shellcmdmenu import ShellCmdMenu


def run_bash_command(command: str) -> str:
    """Execute a bash command on the system.
    Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    if Settings.need_confirm and not confirm(f"Run `{command}`?"):
        raise KeyboardInterrupt("Command execution was canceled by the user")

    menu = ShellCmdMenu(command=command, prompt=f"Running `{command}`")
    menu.exec()
    return menu.get_output()
