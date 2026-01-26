import argparse
import logging
import os
import tempfile
from threading import Event, Thread
from typing import Optional

import requests
from audio.record_audio import record_audio
from utils.getch import getch


def convert_audio_to_text(file: str) -> str:
    logging.info(f"Converting audio to text: {file}")

    # https://platform.openai.com/docs/guides/speech-to-text
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]}
    payload = {"model": "gpt-4o-mini-transcribe"}
    with open(file, "rb") as f:
        files = {
            "file": (
                os.path.basename(file),
                f,
                "application/octet-stream",
            )
        }
        response = requests.post(url, headers=headers, data=payload, files=files)
    json = response.json()
    if "text" not in json:
        raise ValueError(f"Invalid result: {json}")
    return json["text"]


def speech_to_text() -> Optional[str]:
    fd, out_file = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    stop_event = Event()
    t = Thread(target=record_audio, args=(out_file, stop_event))
    t.start()

    try:
        print("Recording... (Press ENTER to finish, ESC to cancel)", end="", flush=True)
        try:
            while True:
                ch = getch()
                if ch in ["\r", "\n"]:
                    print()
                    break
                elif ch == "\x1b":  # ESC
                    print("\nCancelled")
                    return None
        except KeyboardInterrupt:
            print("\nCancelled")
            return None
        finally:
            stop_event.set()
            t.join()

        if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
            return None

        print("Converting audio to text...")
        return convert_audio_to_text(file=out_file)
    finally:
        if os.path.exists(out_file):
            os.remove(out_file)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to the audio file", default=None)
    args = parser.parse_args()

    result: Optional[str]
    if args.file:
        result = convert_audio_to_text(args.file)
    else:
        result = speech_to_text()

    print(result, end="")


if __name__ == "__main__":
    _main()
