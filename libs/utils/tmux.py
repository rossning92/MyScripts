import os
import shutil
import subprocess


def is_in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def is_tmux_installed() -> bool:
    return shutil.which("tmux") is not None


def has_tmux_session() -> bool:
    if not is_tmux_installed():
        return False

    result = subprocess.run(
        ["tmux", "ls"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())
