import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

import requests
from ai.chat import function_to_tool_definition
from ai.tool_use import ToolUse

DEFAULT_MODEL = "gpt-4o"


def complete_chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include_usage: bool = True,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    logging.debug(f"messages: {messages}")

    api_key = os.environ["OPENAI_API_KEY"]
    if not api_key:
        raise Exception("OPENAI_API_KEY must be provided.")

    # https://platform.openai.com/docs/api-reference/responses
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model if model else DEFAULT_MODEL,
        "input": messages,
        "stream": True,
    }
    if system_prompt:
        payload["instructions"] = system_prompt
    if tools:
        # https://platform.openai.com/docs/guides/tools?lang=bash&tool-type=function-calling
        payload["tools"] = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description,
                        }
                        for param in tool.parameters
                    },
                    "required": tool.required,
                    "additionalProperties": False,
                },
                "strict": True,
            }
            for tool in map(function_to_tool_definition, tools)
        ]
    with requests.post(url, headers=headers, json=payload, stream=True) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"HTTP {response.status_code} error: {str(e)}\n"
                f"Text: {response.text}"
            )

        content = ""
        for line in response.iter_lines():
            if not line:
                continue

            logging.debug(f"Received chunk: {line}")

            if line.startswith(b"data: "):
                data = json.loads(line[6:].decode("utf-8"))

                if data["type"] == "response.completed":
                    break
                elif data["type"] == "response.output_text.delta":
                    delta = data["delta"]
                    assert isinstance(delta, str), "Delta must be a string"
                    content += delta
                    yield delta
                if data["type"] == "response.output_item.done":
                    item = data["item"]
                    if item["type"] == "function_call":
                        if on_tool_use:
                            on_tool_use(
                                ToolUse(
                                    tool_name=item["name"],
                                    args=json.loads(item["arguments"]),
                                    tool_use_id=item["id"],
                                )
                            )
                            messages.append(item)


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

    # TODO: Remove create_user_message below
    # for chunk in complete_chat(messages=[create_user_message(input_text, args.image)]):
    #     print(chunk, end="")
