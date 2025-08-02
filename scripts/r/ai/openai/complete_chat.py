import argparse
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import requests
from ai.tokenutil import token_count

DEFAULT_MODEL = "gpt-4o"


def _encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_user_message(text: str, image_file: Optional[str] = None) -> Dict[str, Any]:
    if image_file:
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{_encode_image_base64(image_file)}"
                    },
                },
            ],
        }
    else:
        return {"role": "user", "content": text}


def message_to_str(message: Dict[str, Any]):
    content = message["content"]
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        s = ""
        for c in content:
            if c["type"] == "text":
                s += c["text"]
            elif c["type"] == "image_url":
                s += " <image_url>"
        return s
    else:
        return ""


def complete_chat(
    message: Union[str, List[Dict[str, Any]]],
    image_file: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include_usage: bool = True,
) -> Iterator[str]:
    if isinstance(message, str):
        messages = [create_user_message(text=message, image_file=image_file)]
    else:
        messages = message

    api_key = os.environ["OPENAI_API_KEY"]
    if not api_key:
        raise Exception("OPENAI_API_KEY must be provided.")

    # https://platform.openai.com/docs/api-reference/completions/create
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model if model else DEFAULT_MODEL,
        "messages": (
            [{"role": "system", "content": system_prompt}] if system_prompt else []
        )
        + messages,
        "stream": True,
    }
    if include_usage:
        data["stream_options"] = {"include_usage": True}

    response = requests.post(url, headers=headers, json=data, stream=True)
    response.raise_for_status()
    try:
        for chunk in response.iter_lines():
            if len(chunk) == 0:
                continue

            logging.debug(f"Received chunk: {chunk}")

            if b"DONE" in chunk:
                break

            decoded_line = json.loads(chunk.decode("utf-8").split("data: ")[1])
            choises = decoded_line.get("choices", [])
            if choises:
                token = choises[0]["delta"].get("content")
                if token is not None:
                    yield token

            if include_usage:
                usage = decoded_line.get("usage", None)
                if usage:
                    token_count.input_tokens += usage["prompt_tokens"]
                    token_count.output_tokens += usage["completion_tokens"]

    finally:
        response.close()


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

    for chunk in complete_chat(input_text, image_file=args.image):
        print(chunk, end="")
