import os
import re
import subprocess
import sys
import tempfile

from ai.utils.tools import Settings
from utils.menu.confirmmenu import confirm
from utils.menu.menu import Menu

TRUSTED_COMMANDS = [
    "Get-ChildItem",
    "ls",
    "dir",
    "Get-Location",
    "pwd",
    "Get-Date",
    "date",
    "Get-Content",
    "cat",
    "type",
    "Get-Process",
    "ps",
    "Get-Service",
    "Get-Command",
    "gcm",
    "Get-Help",
    "help",
]


def _strip_transcript(text: str) -> str:
    lines = text.splitlines()

    # Find the start of the actual output
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("Transcript started, output file is"):
            start_idx = i + 1
            break

    # Find the end of the actual output
    end_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("**********************"):
            if (
                i + 1 < len(lines)
                and "Windows PowerShell transcript end" in lines[i + 1]
            ):
                end_idx = i
                break

    return "\n".join(lines[start_idx:end_idx]).strip()


def _run_powershell(command: str) -> str:
    ps_exe = "powershell" if sys.platform == "win32" else "pwsh"

    # Use NamedTemporaryFile to generate random filenames.
    # delete=False is required on Windows because files must be closed before PowerShell
    # can open them (otherwise a sharing violation occurs).
    with tempfile.NamedTemporaryFile(
        suffix=".ps1", delete=False, mode="w", encoding="utf-8-sig"
    ) as f:
        script_file = f.name
        f.write(command)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        log_file = f.name

    try:
        ps_command = [
            ps_exe,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Start-Transcript -Path '{log_file}' -Force; try {{ & '{script_file}' }} finally {{ Stop-Transcript }}",
        ]

        Menu.run_raw(lambda: subprocess.run(ps_command, check=False))

        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            return _strip_transcript(content)

    finally:
        if os.path.exists(script_file):
            os.remove(script_file)
        if os.path.exists(log_file):
            os.remove(log_file)


def powershell(command: str) -> str:
    """
    Execute a PowerShell command on the system.
    - Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    - Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    need_confirm = not any(
        re.match(rf"^\s*{re.escape(cmd)}(?:\s+|$)", command, re.IGNORECASE)
        for cmd in TRUSTED_COMMANDS
    )

    if (
        Settings.need_confirm
        and need_confirm
        and not confirm(f"run in powershell: `{command}`?")
    ):
        raise KeyboardInterrupt("Command execution was canceled by the user")

    return _run_powershell(command)
