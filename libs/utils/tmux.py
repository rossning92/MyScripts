import os


def is_in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))
