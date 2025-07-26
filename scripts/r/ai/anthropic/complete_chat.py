import json
import os
from typing import Any, Dict, Iterator, List, Optional, Union

import requests


def complete_chat(
    message: Union[str, List[Dict[str, Any]]],
    model: str = "claude-3-5-sonnet-latest",
    system_prompt: Optional[str] = None,
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

    # Remove __timestamps key from messages
    for msg in messages:
        if "__timestamp" in msg:
            del msg["__timestamp"]

    payload = {
        # https://docs.anthropic.com/en/docs/about-claude/models
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "stream": True,
    }

    if system_prompt:
        payload["system"] = system_prompt

    with requests.post(api_url, headers=headers, json=payload, stream=True) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"HTTP {response.status_code} error: {str(e)}\n"
                f"Text: {response.text}"
            )

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
                        yield text_chunk

                if json_data.get("type") == "message_stop":
                    break
