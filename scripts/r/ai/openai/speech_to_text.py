import argparse
import logging
import os
from typing import Optional

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
    json = response.json()
    if "text" not in json:
        raise ValueError(f"Invalid result: {json}")
    return json["text"]


def speech_to_text() -> Optional[str]:
    audio_file = record_audio()
    if audio_file:
        text = convert_audio_to_text(audio_file)
        os.remove(audio_file)
        return text
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to the audio file", default=None)
    args = parser.parse_args()

    result: Optional[str]
    if args.file:
        result = convert_audio_to_text(args.file)
    else:
        result = speech_to_text()

    print(result, end="")
