import json
import logging
import os
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
)

import requests
from ai.chat import function_to_tool_definition
from ai.tokenutil import token_count
from ai.tool_use import ToolUse

DEFAULT_MODEL = "claude-3-7-sonnet-latest"


def complete_chat(
    messages: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    logging.debug(f"messages={messages}")

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
    }
    if system_prompt:
        payload["system"] = system_prompt
    if tools:
        payload["tools"] = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description,
                        }
                        for param in tool.parameters
                    },
                    "required": tool.required,
                },
            }
            for tool in [function_to_tool_definition(func) for func in tools]
        ]

    with requests.post(api_url, headers=headers, json=payload, stream=True) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"HTTP {response.status_code} error: {str(e)}\n"
                f"Text: {response.text}"
            )

        text = None
        tool_use = None
        tool_input_json = ""
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
                    break

                elif json_data["type"] == "content_block_start":
                    content_block = json_data["content_block"]
                    if content_block["type"] == "tool_use":
                        tool_use = content_block.copy()
                        tool_input_json = ""
                        if on_tool_use_start:
                            on_tool_use_start(
                                ToolUse(
                                    tool_name=tool_use["name"],
                                    args=tool_use["input"],
                                    tool_use_id=tool_use["id"],
                                )
                            )
                    elif content_block["type"] == "text":
                        text = content_block.copy()

                elif json_data["type"] == "content_block_delta":
                    if json_data["delta"]["type"] == "text_delta":
                        text_chunk = json_data["delta"]["text"]
                        if text_chunk:
                            assert isinstance(text, dict)
                            text["text"] += text_chunk
                            yield text_chunk

                    if json_data["delta"]["type"] == "input_json_delta":
                        tool_input_json += json_data["delta"]["partial_json"]

                elif json_data["type"] == "content_block_stop":
                    if text:
                        text = None
                    elif tool_use:
                        tool_use["input"] = json.loads(tool_input_json)
                        if on_tool_use:
                            on_tool_use(
                                ToolUse(
                                    tool_name=tool_use["name"],
                                    args=tool_use["input"],
                                    tool_use_id=tool_use["id"],
                                )
                            )
                        tool_use = None
                        tool_input_json = ""

                elif json_data["type"] == "error":
                    raise Exception(f"Error from API: {json_data}")
