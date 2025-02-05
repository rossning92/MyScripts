import argparse
import atexit
import os
import signal
import subprocess
import sys
import time
from typing import List, Optional

from _shutil import is_in_termux
from utils.getch import getch


def _run_without_output(command: List[str]):
    with open(os.devnull, "w") as devnull:
        subprocess.check_call(command, stdout=devnull, stderr=devnull)


def _wait_for_key() -> bool:
    sys.stdout.write("Recording (Press [ENTER] to confirm / [Q] to cancel)")
    sys.stdout.flush()
    status: Optional[bool] = None
    while status is None:
        try:
            key = getch()
        except KeyboardInterrupt:
            status = False
        if key == "\n" or key == "\r":
            status = True
        elif key == "q":
            status = False
    if status:
        sys.stdout.write("\nDone.\n")
    else:
        sys.stdout.write("\nCanceled.\n")
    sys.stdout.flush()
    return status


_is_recording_termux = False


def cleanup():
    global _is_recording_termux
    if _is_recording_termux:
        subprocess.check_call(["termux-microphone-record", "-q"])
        _is_recording_termux = False


atexit.register(cleanup)


def record_audio(out_file: Optional[str] = None) -> Optional[str]:
    import tempfile

    global _is_recording_termux

    if out_file is None:
        out_file = tempfile.mktemp(suffix=".mp3")

    # Delete the file if it exists.
    if os.path.exists(out_file):
        os.remove(out_file)

    should_save = False
    if is_in_termux():
        _is_recording_termux = True

        _run_without_output(["termux-microphone-record", "-f", out_file])

        should_save = _wait_for_key()

        _is_recording_termux = False
        _run_without_output(["termux-microphone-record", "-q"])

        # Must wait for a tiny bit of time to make sure that the file is saved correctly.
        time.sleep(0.25)

    elif sys.platform == "linux":
        subprocess.run(["run_script", "r/install_package.py", "sox"], check=True)

        process = subprocess.Popen(["rec", "--no-show-progress", out_file])
        pid = process.pid

        should_save = _wait_for_key()

        os.kill(pid, signal.SIGINT)

    else:
        print("ERROR: Not implemented.", file=sys.stderr)
        sys.exit(1)

    # Delete the recording file if canceled.
    if not should_save and os.path.exists(out_file):
        os.remove(out_file)

    if should_save:
        return out_file
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="The filename to record to")
    args = parser.parse_args()

    record_audio(out_file=args.file)
