import json
import logging
import os
from typing import Any, Dict, Iterator, List, Optional

import requests
from ai.tokenutil import token_count

DEFAULT_MODEL = "claude-3-7-sonnet-latest"


def complete_chat(
    messages: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Any]] = None,
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

    payload = {
        # https://docs.anthropic.com/en/docs/about-claude/models
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "stream": True,
        **({"tools": tools} if tools else {}),
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

        text_content = ""
        tool_uses: List[Any] = []
        tool_input_json = ""
        current_tool = None
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                logging.debug(f"Received line: {decoded_line}")

                if not decoded_line.startswith("data: "):
                    continue

                json_data = json.loads(decoded_line[6:])

                if json_data["type"] == "message_start":
                    token_count.input_tokens += json_data["message"]["usage"][
                        "input_tokens"
                    ]
                    token_count.output_tokens += json_data["message"]["usage"][
                        "output_tokens"
                    ]

                elif json_data["type"] == "message_delta":
                    token_count.output_tokens += json_data["usage"]["output_tokens"]

                elif json_data["type"] == "message_stop":
                    content = []
                    if text_content:
                        content.append({"type": "text", "text": text_content})
                    if tool_uses:
                        content.extend(tool_uses)
                    messages.append({"role": "assistant", "content": content})
                    break

                elif json_data["type"] == "content_block_start":
                    content_block = json_data["content_block"]
                    if content_block["type"] == "tool_use":
                        current_tool = content_block.copy()
                        tool_input_json = ""

                elif json_data["type"] == "content_block_delta":
                    if json_data["delta"]["type"] == "text_delta":
                        text_chunk = json_data["delta"]["text"]
                        if text_chunk:
                            text_content += text_chunk
                            yield text_chunk

                    if json_data["delta"]["type"] == "input_json_delta":
                        tool_input_json += json_data["delta"]["partial_json"]

                elif json_data["type"] == "content_block_stop":
                    if current_tool:
                        current_tool["input"] = json.loads(tool_input_json)
                        tool_uses.append(current_tool)
                        current_tool = None
                        tool_input_json = ""

                elif json_data["type"] == "error":
                    raise Exception(f"Error from API: {json_data}")
