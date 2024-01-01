import os
import subprocess
import tempfile
from typing import Optional

import requests


def text_to_speech_openai(text: str, out_file: Optional[str] = None):
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f'Bearer {os.environ["OPENAI_API_KEY"]}',
            "Content-Type": "application/json",
        },
        json={
            "model": "tts-1",
            "input": text,
            "voice": "alloy",
        },
    )

    if response.status_code == 200:
        if out_file is None:
            tmpfile = os.path.join(tempfile.gettempdir(), "speech.mp3")
            with open(tmpfile, "wb") as file:
                file.write(response.content)
            subprocess.check_call(["mpv", tmpfile])
            os.remove(tmpfile)
        else:
            with open(out_file, "wb") as file:
                file.write(response.content)
    else:
        raise Exception(response.text)


def text_to_speech(text: str):
    text_to_speech_openai(text=text)


if __name__ == "__main__":
    text_to_speech(
        "Today is a wonderful day to build something people love!",
    )
