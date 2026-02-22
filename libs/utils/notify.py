import subprocess
from pathlib import Path

from .platform import is_linux, is_termux, is_windows
from .script.path import get_my_script_root


def send_notify(text: str):
    if is_termux():
        subprocess.run(
            ["termux-notification", "-c", text, "--vibrate", "500"], check=True
        )
    elif is_linux():
        subprocess.run(["notify-send", text], check=True)
    elif is_windows():
        script_path = (
            Path(get_my_script_root()) / "scripts" / "ext" / "send_notification.ps1"
        )
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                text,
            ],
            check=True,
        )
