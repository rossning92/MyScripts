import os
import subprocess
from typing import List


def _run_without_output(command: List[str]):
    with open(os.devnull, "w") as devnull:
        subprocess.check_call(command, stdout=devnull, stderr=devnull)


def play(file: str):
    _run_without_output(["mpv", file])
