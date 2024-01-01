import shutil
import sys
from functools import lru_cache


@lru_cache(maxsize=None)
def is_termux():
    return shutil.which("termux-setup-storage") is not None


def is_linux():
    return sys.platform == "linux"


def is_windows():
    return sys.platform == "win32"


def is_mac():
    return sys.platform == "darwin"
