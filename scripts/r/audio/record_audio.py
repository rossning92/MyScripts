import argparse
import os
import signal
import subprocess
import sys
from typing import Optional

from _pkgmanager import require_package
from _shutil import is_in_termux
from utils.getch import getch


def _wait_for_key() -> bool:
    sys.stdout.write("Recording (Press Enter to confirm or Q to cancel)")
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


def initialize_pulseaudio():
    if is_in_termux():
        require_package("pulseaudio")
        subprocess.call(
            ["pulseaudio", "-k"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(["pulseaudio", "-L", "module-sles-source", "-D"])


def record_audio(out_file: Optional[str] = None) -> Optional[str]:
    import tempfile

    global _is_recording_termux

    if out_file is None:
        out_file = tempfile.mktemp(suffix=".mp3")

    # Delete the file if it exists.
    if os.path.exists(out_file):
        os.remove(out_file)

    should_save = False
    if sys.platform == "linux":
        require_package("sox")

        if is_in_termux():
            initialize_pulseaudio()

        process = subprocess.Popen(
            [
                "rec",
                "--no-show-progress",
                "-V1",  # only show failure messages
                out_file,
            ]
        )
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
    import datetime

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, nargs="?", help="The filename to record to")
    args = parser.parse_args()

    if not args.file:
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.file = f"recording_{current_time}.wav"

    record_audio(out_file=args.file)
