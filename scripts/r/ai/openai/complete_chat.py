import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import requests

DEFAULT_MODEL = "gpt-4o"


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def complete_chat(
    message: Union[str, List[Dict[str, Any]]],
    image: Optional[str] = None,
    model: Optional[str] = None,
) -> Iterator[str]:
    if image is not None:
        if not isinstance(message, str):
            raise Exception("Message must be a str")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encode_image(image)}"
                        },
                    },
                ],
            }
        ]
    elif isinstance(message, str):
        messages = [{"role": "user", "content": message}]
    else:
        messages = message

    api_key = os.environ["OPENAI_API_KEY"]
    if not api_key:
        raise Exception("OPENAI_API_KEY must be provided.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model if model else DEFAULT_MODEL,
        "messages": messages,
        "stream": True,
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    response.raise_for_status()
    content = ""
    for chunk in response.iter_lines():
        if len(chunk) == 0:
            continue

        if b"DONE" in chunk:
            break

        try:
            decoded_line = json.loads(chunk.decode("utf-8").split("data: ")[1])
            token = decoded_line["choices"][0]["delta"].get("content")

            if token is not None:
                content += token
                yield token

        except GeneratorExit:
            break

    messages.append({"role": "assistant", "content": content})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str)
    parser.add_argument("--image", type=Path)
    args = parser.parse_args()

    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input

    for chunk in complete_chat(input_text, image=args.image):
        print(chunk, end="")
