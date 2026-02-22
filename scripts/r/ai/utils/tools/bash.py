import os
import re
import subprocess
import sys
import tempfile

from ai.utils.tools import Settings
from utils.menu.confirmmenu import confirm
from utils.menu.menu import Menu
from utils.menu.shellcmdmenu import ShellCmdMenu
from utils.term import clear_terminal


def _run_script(command: str, log_file: str) -> None:
    clear_terminal()
    subprocess.run(["script", "-q", "-e", "-c", command, log_file], check=False)


TRUSTED_COMMANDS = ["ls", "pwd", "date"]


def _run_bash(command: str) -> str:
    # Use a temporary file to capture command output
    with tempfile.NamedTemporaryFile(delete=False) as f:
        log_file = f.name

    try:
        # Run command interactively using 'script' (-q: quiet, -e: return exit code, -c: run command)
        Menu.run_raw(lambda: _run_script(command, log_file))

        # Read the captured output
        with open(log_file, "r") as f:
            output = f.read()

        output = re.sub(r"^Script started on .*\n?", "", output)
        output = re.sub(r"Script done on .*", "", output.strip())
        return output.replace("\r", "").strip()
    finally:
        # Clean up the temporary file
        if os.path.exists(log_file):
            os.remove(log_file)


def bash(command: str) -> str:
    """
    Execute a bash command on the system.
    - Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    - Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    need_confirm = True
    for cmd in TRUSTED_COMMANDS:
        pattern = re.escape(cmd).replace(r"\*", ".*")
        if re.match(rf"^\s*{pattern}(?:\s+|$)", command):
            need_confirm = False
            break

    if Settings.need_confirm and need_confirm and not confirm(f"Run `{command}`?"):
        raise KeyboardInterrupt("Command execution was canceled by the user")

    if sys.platform == "win32":
        menu = ShellCmdMenu(command=command, prompt=f"Running `{command}`")
        menu.exec()
        return menu.get_output()
    else:
        return _run_bash(command)
