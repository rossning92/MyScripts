import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests
from ai.chat import create_user_message
from ai.tokenutil import token_count

DEFAULT_MODEL = "gpt-4o"


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
                s += "<image_url/>"
            elif c["type"] == "tool_use":
                s += f"<tool_use>{c}</tool_use>"
            elif c["type"] == "tool_result":
                s += f"<tool_result>{c}</tool_result>"
        return s
    else:
        return ""


def complete_chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include_usage: bool = True,
) -> Iterator[str]:
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
    content = ""
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
                    content += token
                    yield token

            if include_usage:
                usage = decoded_line.get("usage", None)
                if usage:
                    token_count.input_tokens += usage["prompt_tokens"]
                    token_count.output_tokens += usage["completion_tokens"]

    finally:
        response.close()
        messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )


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

    for chunk in complete_chat(messages=[create_user_message(input_text, args.image)]):
        print(chunk, end="")
