import argparse
import os
import signal
import subprocess
import sys
import tempfile
from threading import Event, Thread
from typing import Optional

from _pkgmanager import require_package
from utils.getch import getch
from utils.retry import retry
from utils.termux import is_in_termux


def _wait_for_key() -> bool:
    success: Optional[bool] = None
    while success is None:
        for indicator in "|/-\\":
            sys.stdout.write(f"\rRecording... {indicator} ([Enter] Stop [q] Cancel)")
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
        subprocess.check_call(
            ["pulseaudio", "-L", "module-sles-source", "-D"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def record_audio(
    out_file: Optional[str] = None,
    stop_event: Optional[Event] = None,
) -> str:
    if sys.platform != "linux":
        raise NotImplementedError()

    if out_file is None:
        fd, out_file = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    if os.path.exists(out_file):
        os.remove(out_file)

    require_package("sox")

    if is_in_termux():
        _initialize_pulseaudio()

    process = subprocess.Popen(
        [
            "rec",
            "--buffer",
            "1024",
            "--no-show-progress",
            "-V1",  # Only show failure messages
            "-r",
            "16000",  # Sample rate: 16kHz
            "-c",
            "1",  # Number of channels
            "-C",
            "32",  # MP3 bitrate in kbps (optimal for 16kHz voice)
            out_file,
            "highpass",
            "100",  # Remove low-frequency noise (optimal for voice)
        ]
    )

    if stop_event:
        stop_event.wait()
        process.send_signal(signal.SIGINT)

    process.wait()

    return out_file


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, nargs="?", help="The filename to record to")
    args = parser.parse_args()

    # Start recording
    stop_event = Event()
    out_file = None

    def _record_audio_task():
        nonlocal out_file
        out_file = record_audio(out_file=args.file, stop_event=stop_event)

    t = Thread(target=_record_audio_task)
    t.start()

    # Wait to stop recording
    should_save = _wait_for_key()
    stop_event.set()
    t.join()

    # Delete the recording file if canceled
    if out_file and not should_save and os.path.exists(out_file):
        os.remove(out_file)


if __name__ == "__main__":
    _main()
