import argparse
import datetime
import os
import signal
import subprocess
import sys
from threading import Event, Thread
from typing import Optional

from _pkgmanager import require_package
from _shutil import is_in_termux
from utils.getch import getch
from utils.retry import retry


def _wait_for_key() -> bool:
    success: Optional[bool] = None
    while success is None:
        for indicator in "|/-\\":
            sys.stdout.write(
                f"\rRecording {indicator} (Press 'Enter' to confirm or 'q' to cancel)"
            )
            sys.stdout.flush()
            try:
                key = getch(timeout=0.5)
            except KeyboardInterrupt:
                success = False
            if key in ["\n", "\r", " "]:
                success = True
            elif key in ["q", "\x1b"]:
                success = False
    if success:
        sys.stdout.write("\nDone\n")
    else:
        sys.stdout.write("\nCanceled\n")
    sys.stdout.flush()
    return success


@retry()
def _initialize_pulseaudio():
    if is_in_termux():
        require_package("pulseaudio")
        subprocess.call(
            ["pulseaudio", "-k"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(["pulseaudio", "-L", "module-sles-source", "-D"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def record_audio(out_file: str, stop_event: Optional[Event] = None) -> Optional[str]:
    if sys.platform != "linux":
        raise NotImplementedError()

    # Delete the file if it exists
    if os.path.exists(out_file):
        os.remove(out_file)

    require_package("sox")

    if is_in_termux():
        _initialize_pulseaudio()

    process = subprocess.Popen(
        [
            "rec",
            "--no-show-progress",
            "-V1",  # only show failure messages
            "-r",
            "16000",
            "-c",
            "1",
            "-b",
            "16",
            out_file,
        ]
    )

    if stop_event and stop_event.wait():
        process.send_signal(signal.SIGINT)
    else:
        process.wait()

    return out_file


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, nargs="?", help="The filename to record to")
    args = parser.parse_args()

    out_file = args.file
    if not out_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        out_file = f"recording_{timestamp}.mp3"

    # Start recording
    stop_event = Event()
    t = Thread(
        target=record_audio,
        kwargs={"out_file": out_file, "stop_event": stop_event},
    )
    t.start()

    # Wait to stop recording
    should_save = _wait_for_key()
    stop_event.set()
    t.join()

    # Delete the recording file if canceled
    if not should_save and os.path.exists(out_file):
        os.remove(out_file)


if __name__ == "__main__":
    _main()
