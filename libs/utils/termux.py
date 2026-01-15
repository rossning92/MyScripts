import shutil
from functools import lru_cache


@lru_cache(maxsize=None)
def is_in_termux():
    return shutil.which("termux-setup-storage") is not None
