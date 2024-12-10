import json
import os
from typing import Any, Dict, Iterator, List, Union

import requests


def complete_chat(
    message: Union[str, List[Dict[str, Any]]],
) -> Iterator[str]:

    api_key = os.environ["ANTHROPIC_API_KEY"]
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY must be provided.")

    # https://docs.anthropic.com/en/api/messages-examples
    api_url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    if isinstance(message, str):
        messages = [{"role": "user", "content": message}]
    else:
        messages = message

    payload = {
        # https://docs.anthropic.com/en/docs/about-claude/models
        "model": "claude-3-5-sonnet-latest",
        "messages": messages,
        "max_tokens": 4096,
        "stream": True,
    }

    content = ""
    with requests.post(api_url, headers=headers, json=payload, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")

                if not decoded_line.startswith("data: "):
                    continue

                json_data = json.loads(decoded_line[6:])
                if (
                    json_data.get("type") == "content_block_delta"
                    and json_data.get("delta", {}).get("type") == "text_delta"
                ):
                    text_chunk = json_data["delta"].get("text", "")
                    if text_chunk:
                        content += text_chunk
                        yield text_chunk

                if json_data.get("type") == "message_stop":
                    break

    messages.append({"role": "assistant", "content": content})
