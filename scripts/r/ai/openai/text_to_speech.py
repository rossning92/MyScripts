import argparse
import os
import subprocess
from typing import Optional

import requests


def text_to_speech(text: str, out_file: Optional[str] = None):
    format = os.path.splitext(out_file)[1].lstrip(".") if out_file else "mp3"
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
            "response_format": format,
        },
        stream=True,
    )

    if response.status_code == 200:
        if out_file:
            with open(out_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=None):
                    f.write(chunk)
        else:
            process = subprocess.Popen(
                # ["ffplay", "-fs", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
                ["play", "--volume", "2", "-q", "-t", format, "-"],
                stdin=subprocess.PIPE,
            )
            assert process.stdin is not None
            for chunk in response.iter_content(chunk_size=None):
                process.stdin.write(chunk)
            process.stdin.close()
            process.wait()
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
    parser.add_argument(
        "-o",
        "--out_file",
        type=str,
        help="Output file to save the speech audio (default: play directly)",
    )
    args = parser.parse_args()

    text_to_speech(args.text, out_file=args.out_file)
