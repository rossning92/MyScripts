import argparse
import os
import tempfile
from typing import Optional

import requests
from utils.playback import play


def text_to_speech(text: str, out_file: Optional[str] = None):
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

            play(tmpfile)

            os.remove(tmpfile)

        else:
            with open(out_file, "wb") as file:
                file.write(response.content)
    else:
        raise Exception(response.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "text",
        type=str,
        nargs="?",
        default="Today is a wonderful day to build something people love!",
        help="Text to be converted to speech",
    )
    args = parser.parse_args()

    text_to_speech(args.text)
