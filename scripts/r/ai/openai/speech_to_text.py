import argparse
import logging
import os
import tempfile

import requests
from audio.record_audio import record_audio


def convert_audio_to_text(file: str) -> str:
    logging.info(f"Converting audio to text: {file}")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]}
    payload = {"model": "whisper-1"}
    files = {
        "file": (
            os.path.basename(file),
            open(file, "rb"),
            "application/octet-stream",
        )
    }
    response = requests.post(url, headers=headers, data=payload, files=files)
    text = response.json()["text"]
    return text


def speech_to_text() -> str:
    record_file = os.path.join(tempfile.gettempdir(), "record.mp3")
    try:
        record_audio(record_file)
        return convert_audio_to_text(record_file)
    finally:
        os.remove(record_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to the audio file", default=None)
    args = parser.parse_args()

    if args.file:
        result = convert_audio_to_text(args.file)
    else:
        result = speech_to_text()
    print(result)
