from typing import Optional

from ..menu import Menu


def select_option(options, history: Optional[str] = None):
    if not options:
        raise Exception("Options cannot be empty.")
    return Menu(items=options, history=history).exec()
