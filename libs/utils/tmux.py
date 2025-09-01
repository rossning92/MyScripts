import os
import shutil
import subprocess


def is_in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def is_tmux_installed() -> bool:
    return shutil.which("tmux") is not None


def has_tmux_session() -> bool:
    return is_tmux_installed() and (
        subprocess.call(
            ["tmux", "ls"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        == 0
    )
