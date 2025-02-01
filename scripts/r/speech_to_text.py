import argparse
import json
import subprocess
from typing import Optional

from ai.openai.speech_to_text import speech_to_text as speech_to_text_openai
from utils.platform import is_termux


def speech_to_text_termux() -> Optional[str]:
    out = subprocess.check_output(["termux-dialog", "speech"], universal_newlines=True)
    data = json.loads(out)
    if data["code"] == 0:
        return data["text"]
    else:
        return None


def speech_to_text() -> Optional[str]:
    # if is_termux():
    #     return speech_to_text_termux()
    # else:
    return speech_to_text_openai()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output", type=str, help="Path to the output text file", default=None
    )
    args = parser.parse_args()

    text = speech_to_text()
    if text is not None:
        print(text)

        if args.output:
            with open(args.output, "w") as f:
                f.write(text)
