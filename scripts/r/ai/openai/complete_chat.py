import argparse
import json
import os
import sys
from typing import Dict, Iterator, List, Optional

import requests


def complete_messages(
    messages: List[Dict[str, str]], model: Optional[str] = None
) -> Iterator[str]:
    api_key = os.environ["OPENAI_API_KEY"]
    if not api_key:
        raise Exception("OPENAI_API_KEY must be provided.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model if model else "gpt-4o",
        "messages": messages,
        "stream": True,
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    response.raise_for_status()
    for chunk in response.iter_lines():
        if len(chunk) == 0:
            continue

        if b"DONE" in chunk:
            break

        try:
            decoded_line = json.loads(chunk.decode("utf-8").split("data: ")[1])
            token = decoded_line["choices"][0]["delta"].get("content")

            if token is not None:
                yield token

        except GeneratorExit:
            break


def complete_message(input_text: str) -> str:
    result = ""
    for chunk in complete_messages([{"role": "user", "content": input_text}]):
        result += chunk
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str, help="Input input")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input

    for chunk in complete_messages([{"role": "user", "content": input_text}]):
        print(chunk, end="")
