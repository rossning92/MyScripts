import argparse
import atexit
import os
import signal
import subprocess
import sys
import time

from _shutil import is_in_termux
from utils.getch import getch


def wait_stop():
    print("(press 'q' to stop recording...)")
    while getch() != "q":
        pass


_is_recording_termux = False


def cleanup():
    global _is_recording_termux
    if _is_recording_termux:
        subprocess.check_call(["termux-microphone-record", "-q"])
        _is_recording_termux = False


atexit.register(cleanup)


def record_audio(out_file: str):
    global _is_recording_termux

    if is_in_termux():
        _is_recording_termux = True
        subprocess.check_call(["termux-microphone-record", "-f", out_file])

        wait_stop()

        _is_recording_termux = False
        subprocess.check_call(["termux-microphone-record", "-q"])
        time.sleep(1)  # HACK: wait for 1 second until the file is saved.

    elif sys.platform == "linux":
        subprocess.run(["run_script", "r/install_package.py", "sox"], check=True)

        process = subprocess.Popen(["rec", "--no-show-progress", out_file])
        pid = process.pid

        wait_stop()

        os.kill(pid, signal.SIGINT)
    else:
        print("ERROR: not implemented.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record audio.")
    parser.add_argument("file", type=str, help="The filename to record to")
    args = parser.parse_args()

    record_audio(out_file=args.file)
