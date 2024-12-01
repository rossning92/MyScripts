import argparse
import atexit
import os
import signal
import subprocess
import sys
import time
from typing import Optional

from _shutil import is_in_termux
from utils.getch import getch


def _wait_for_key() -> bool:
    print("(Press 'Enter' to continue, 'q' to cancel)")
    while True:
        try:
            key = getch()
        except KeyboardInterrupt:
            return False
        if key == "\n" or key == "\r":
            return True
        elif key == "q":
            return False


_is_recording_termux = False


def cleanup():
    global _is_recording_termux
    if _is_recording_termux:
        subprocess.check_call(["termux-microphone-record", "-q"])
        _is_recording_termux = False


atexit.register(cleanup)


def record_audio(out_file: str) -> Optional[str]:
    global _is_recording_termux

    saved = False
    if is_in_termux():
        _is_recording_termux = True
        subprocess.check_call(["termux-microphone-record", "-f", out_file])

        saved = _wait_for_key()

        _is_recording_termux = False
        subprocess.check_call(["termux-microphone-record", "-q"])
        time.sleep(1)  # HACK: wait for 1 second until the file is saved.

    elif sys.platform == "linux":
        subprocess.run(["run_script", "r/install_package.py", "sox"], check=True)

        process = subprocess.Popen(["rec", "--no-show-progress", out_file])
        pid = process.pid

        saved = _wait_for_key()

        os.kill(pid, signal.SIGINT)

    else:
        print("ERROR: not implemented.", file=sys.stderr)
        sys.exit(1)

    # Delete the recording file if canceled.
    if not saved and os.path.exists(out_file):
        os.remove(out_file)

    if saved:
        return out_file
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="The filename to record to")
    args = parser.parse_args()

    record_audio(out_file=args.file)
