import subprocess
import sys


def send_notify(text: str):
    if sys.platform == "linux":
        subprocess.run(["notify-send", text], check=True)
