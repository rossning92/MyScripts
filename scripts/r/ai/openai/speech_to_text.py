import argparse
import logging
import os
from typing import Optional

import requests
from utils.menu.asynctaskmenu import AsyncTaskMenu
from utils.menu.recordmenu import RecordMenu


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
    record_menu = RecordMenu()
    record_menu.exec()
    out_file = record_menu.get_output_file()
    if not out_file:
        return None

    if not os.path.exists(out_file):
        return None

    async_task_menu = AsyncTaskMenu(
        lambda: convert_audio_to_text(file=out_file),
        prompt="convert audio to text",
    )
    try:
        async_task_menu.exec()
    except ValueError:
        return None
    return async_task_menu.get_result()


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
