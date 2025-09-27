import base64
import json
import logging
import os
from typing import Any, Callable, Dict, Iterator, List, Optional

import requests
from ai.message import Message
from ai.tool_use import ToolUse, function_to_tool_definition

DEFAULT_MODEL = "gpt-4o"


def _encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _to_openai_message_content(message: Message) -> List[Dict[str, Any]]:
    content = []

    if message["text"]:
        content.append(
            {
                "type": "input_text" if message["role"] == "user" else "output_text",
                "text": message["text"],
            }
        )

    if "image_file" in message:
        content.append(
            {
                "type": "input_image",
                "image_url": "data:image/jpeg;base64,{}".format(
                    _encode_image_base64(message["image_file"])
                ),
            }
        )

    return content


def _to_openai_responses_api_input(messages: List[Message]) -> List[Dict[str, Any]]:
    input = []

    for message in messages:
        content = _to_openai_message_content(message)
        if content:
            input.append(
                {
                    "role": message["role"],
                    "content": content,
                }
            )

        for tool_use in message.get("tool_use", []):
            input.append(
                {
                    "type": "function_call",
                    "name": tool_use["tool_name"],
                    "call_id": tool_use["tool_use_id"],
                    "arguments": json.dumps(tool_use["args"]),
                }
            )

        for tool_result in message.get("tool_result", []):
            input.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_result["tool_use_id"],
                    "output": tool_result["content"],
                }
            )

    return input


def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include_usage: bool = True,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    web_search=False,
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

    payload: Dict[str, Any] = {}

    if model:
        # https://platform.openai.com/docs/guides/reasoning
        if model.endswith("(low)"):
            model = model[:-5]
            payload["reasoning"] = {"effort": "low"}
        elif model.endswith("(medium)"):
            model = model[:-8]
            payload["reasoning"] = {"effort": "medium"}
        elif model.endswith("(high)"):
            model = model[:-6]
            payload["reasoning"] = {"effort": "high"}

    payload.update(
        {
            "model": model if model else DEFAULT_MODEL,
            "input": _to_openai_responses_api_input(messages),
            "stream": True,
        }
    )

    if system_prompt:
        payload["instructions"] = system_prompt

    payload_tools: List[Dict[str, Any]] = []

    if tools:
        # https://platform.openai.com/docs/guides/tools?lang=bash&tool-type=function-calling
        payload_tools.extend(
            [
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
        )

    if web_search:
        # https://platform.openai.com/docs/guides/tools-web-search?api-mode=chat#sources
        payload_tools.append({"type": "web_search"})

    if payload_tools:
        payload["tools"] = payload_tools

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
                elif data["type"] == "response.output_item.added":
                    item = data["item"]
                    if item["type"] == "function_call":
                        if on_tool_use_start:
                            on_tool_use_start(
                                ToolUse(
                                    tool_name=item["name"],
                                    args={},
                                    tool_use_id=item["id"],
                                )
                            )
                elif data["type"] == "response.output_item.done":
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
