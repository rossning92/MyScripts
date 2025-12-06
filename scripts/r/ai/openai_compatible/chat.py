import json
import logging
import os
from pprint import pformat
from typing import AsyncIterator, Callable, Dict, List, Optional, cast

import aiohttp
from ai.message import Message
from ai.tool_use import ToolDefinition, ToolUse
from utils.http import check_for_status


async def complete_chat(
    messages: List[Message],
    endpoint_url: str,
    api_key: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[ToolDefinition]] = None,
    on_image: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    on_reasoning: Optional[Callable[[str], None]] = None,
    extra_payload: Optional[Dict] = None,
    out_message: Optional[Message] = None,
) -> AsyncIterator[str]:
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
                                **param.type,
                                "description": param.description,
                            }
                            for param in tool.parameters
                        },
                        "required": tool.required,
                    },
                },
            }
            for tool in tools
        ]

    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})

    for message in messages:
        # Message
        if message["text"] or message.get("tool_use"):
            m = {
                "role": message["role"],
                "content": [
                    {"type": "text", "text": message["text"]},
                ]
                + [
                    {"type": "image_url", "image_url": {"url": url}}
                    for url in message.get("image_urls", [])
                ],
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

            if "reasoning_details" in message:
                m["reasoning_details"] = message["reasoning_details"]

            payload["messages"].append(m)

        # Tool call result
        for tool_result in message.get("tool_result", []):
            payload["messages"].append(
                {
                    "role": "tool",
                    "tool_call_id": tool_result["tool_use_id"],
                    "content": tool_result["content"],
                }
            )

    if extra_payload:
        payload.update(extra_payload)

    logging.debug(f"=== payload ===\n{pformat(payload, width=200)}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint_url,
            headers=headers,
            json=payload,
        ) as response:
            await check_for_status(response)

            buffer = b""
            async for chunk in response.content.iter_chunked(64 * 1024):
                buffer += chunk

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    if not line:
                        continue

                    if not line.startswith(b"data: "):
                        continue

                    data_str = line[6:].decode("utf-8")
                    if data_str == "[DONE]":
                        return

                    try:
                        data = json.loads(data_str)
                        logging.debug(f"=== data ===\n{pformat(data, width=200)}")
                    except json.JSONDecodeError:
                        logging.debug(f"Skipping malformed chunk: {data_str}")
                        continue

                    for choice in data.get("choices", []):
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

                        reasoning_details = delta.get("reasoning_details")
                        if reasoning_details:
                            assert isinstance(reasoning_details, list)
                            for reasoning_detail in reasoning_details:
                                if reasoning_detail["type"] == "reasoning.text":
                                    reasoning_text = reasoning_detail["text"]
                                    if on_reasoning:
                                        on_reasoning(reasoning_text)
                                    if out_message:
                                        out_message.setdefault("reasoning", []).append(
                                            reasoning_text
                                        )

                            if out_message:
                                cast(dict, out_message).setdefault(
                                    "reasoning_details", []
                                ).extend(reasoning_details)

                        images = delta.get("images")
                        if images:
                            assert isinstance(images, list)
                            for image in images:
                                if image["type"] == "image_url":
                                    image_url: str = image["image_url"]["url"]
                                    if on_image:
                                        on_image(image_url)
                                    if out_message:
                                        out_message["image_urls"] = [image_url]
