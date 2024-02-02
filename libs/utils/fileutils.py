import os
from typing import Optional


def read_last_line(file: str) -> str:
    with open(file, "rb") as f:
        try:  # catch OSError in case of a one line file
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
        return last_line


def read_last_non_empty_line(file: str) -> Optional[str]:
    with open(file, "r") as f:
        lines = f.read().splitlines()
    for line in reversed(lines):
        if line != "":
            return line
    return None
