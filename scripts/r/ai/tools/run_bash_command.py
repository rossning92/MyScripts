from utils.menu.confirmmenu import ConfirmMenu
from utils.menu.shellcmdmenu import ShellCmdMenu


def run_bash_command(command: str) -> str:
    """Execute a bash command on the system.
    Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    confirm_menu = ConfirmMenu(prompt=f"Run command: `{command}`?")
    confirm_menu.exec()
    if not confirm_menu.is_confirmed():
        raise KeyboardInterrupt("Command execution was canceled by the user")

    menu = ShellCmdMenu(command=command, prompt=f"Running `{command}`")
    menu.exec()
    return menu.get_output()
