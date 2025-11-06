import json
import logging
import os
from pprint import pformat
from typing import Any, Callable, Iterator, List, Optional

import requests
from ai.message import Message
from ai.tool_use import ToolUse, function_to_tool_definition


def complete_chat(
    messages: List[Message],
    endpoint_url: str,
    api_key: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    logging.debug(f"messages: {messages}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "model": model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "messages": [],
        "stream": True,
    }

    if tools:
        # https://openrouter.ai/docs/features/tool-calling
        payload["tools"] = [
            {
                "type": "function",
                "function": {
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
                    },
                },
            }
            for tool in map(function_to_tool_definition, tools)
        ]

    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})

    for message in messages:
        if message["text"] or message.get("tool_use"):
            payload["messages"].append(
                {
                    "role": message["role"],
                    "content": message["text"],
                    **(
                        {
                            "tool_calls": [
                                {
                                    "id": tool_use["tool_use_id"],
                                    "type": "function",
                                    "function": {
                                        "name": tool_use["tool_name"],
                                        "arguments": json.dumps(tool_use["args"]),
                                    },
                                }
                                for tool_use in message["tool_use"]
                            ]
                        }
                        if "tool_use" in message
                        else {}
                    ),
                }
            )

        for tool_result in message.get("tool_result", []):
            payload["messages"].append(
                {
                    "role": "tool",
                    "tool_call_id": tool_result["tool_use_id"],
                    "content": tool_result["content"],
                }
            )

    logging.debug(f"=== payload ===\n{pformat(payload)}")

    with requests.post(
        endpoint_url, headers=headers, json=payload, stream=True, timeout=60
    ) as response:
        logging.debug(f"response status: {response.status_code}")
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            if not line.startswith("data: "):
                continue

            data = line[6:]
            if data == "[DONE]":
                break

            try:
                chunk = json.loads(data)
                logging.debug(f"=== data ===\n{pformat(chunk)}")
            except json.JSONDecodeError:
                logging.debug(f"Skipping malformed chunk: {data}")
                continue

            for choice in chunk.get("choices", []):
                delta = choice.get("delta", {})

                tool_calls = delta.get("tool_calls")
                if tool_calls:
                    logging.debug(f"tool call delta: {tool_calls}")
                    for tool_call in tool_calls:
                        if tool_call["type"] == "function":
                            function = tool_call["function"]
                            if function and on_tool_use:
                                on_tool_use(
                                    ToolUse(
                                        tool_name=function["name"],
                                        args=json.loads(function["arguments"]),
                                        tool_use_id=tool_call["id"],
                                    )
                                )

                content = delta.get("content")
                if content:
                    logging.debug(f"yielding content chunk: {content}")
                    yield content
