import json
import logging
import os
import uuid
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import aiohttp
from ai.utils.message import Message
from ai.utils.tooluse import ToolDefinition, ToolUse
from ai.utils.usagemetadata import UsageMetadata
from utils.http import check_for_status, iter_lines
from utils.imagedataurl import parse_image_data_url

logger = logging.getLogger(__name__)


# Gemini API does not support "additionalProperties" in JSON Schema.
def _strip_additional_properties(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _strip_additional_properties(v)
            for k, v in value.items()
            if k != "additionalProperties"
        }
    if isinstance(value, list):
        return [_strip_additional_properties(v) for v in value]
    return value


# Doc: https://ai.google.dev/gemini-api/docs/function-calling
def _to_gemini_tools(
    tools: Optional[List[ToolDefinition]] = None,
    web_search: bool = False,
) -> List[Dict[str, Any]]:
    gemini_tools: List[Dict[str, Any]] = []
    if tools:
        function_declarations: List[Dict[str, Any]] = []
        for t in tools:
            properties: Dict[str, Any] = {}
            for p in t.parameters:
                properties[p.name] = {
                    **_strip_additional_properties(p.type),
                    "description": p.description,
                }

            function_declarations.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": t.required,
                    },
                }
            )
        gemini_tools.append({"functionDeclarations": function_declarations})

    if web_search:
        gemini_tools.append({"google_search": {}})

    return gemini_tools


def _build_tool_name_by_id(messages: List[Message]) -> Dict[str, str]:
    tool_name_by_id: Dict[str, str] = {}
    for message in messages:
        for tool_use in message.get("tool_use", []):
            tool_use_id = tool_use["tool_use_id"]
            tool_name = tool_use["tool_name"]
            tool_name_by_id[tool_use_id] = tool_name
    return tool_name_by_id


def _to_gemini_role(role: str) -> str:
    if role == "assistant":
        return "model"
    if role == "user":
        return "user"
    raise ValueError(f"Invalid role: {role}")


def _message_to_parts(message: Message, tool_name_by_id: Dict[str, str]):
    parts = []

    # Function calls (tool uses)
    for tool_use in message.get("tool_use", []):
        thought_signature = tool_use.get("thoughtSignature")
        parts.append(
            {
                "functionCall": {
                    "name": tool_use["tool_name"],
                    "args": tool_use.get("args", {}),
                },
                **(
                    {"thoughtSignature": thought_signature} if thought_signature else {}
                ),
            }
        )

    # Function responses (tool results)
    for tool_result in message.get("tool_result", []):
        tool_name = tool_name_by_id[tool_result["tool_use_id"]]
        parts.append(
            {
                "functionResponse": {
                    "name": tool_name,
                    "response": {"result": tool_result.get("content", "")},
                }
            }
        )

    # Text
    text = message.get("text")
    if text:
        parts.append({"text": text})

    # Images
    image_urls = message.get("image_urls", [])
    for url in image_urls:
        if not url:
            continue
        if url.startswith("data:"):
            result = parse_image_data_url(url)
            parts.append(
                {
                    "inline_data": {
                        "mime_type": result.mime_type,
                        "data": result.data,
                    }
                }
            )
        else:
            parts.append(
                {
                    "file_data": {
                        "mime_type": "application/octet-stream",
                        "file_uri": url,
                    }
                }
            )

    return parts


async def complete_chat(
    messages: List[Message],
    out_message: Message,
    model: str,
    system_prompt: Optional[str] = None,
    tools: Optional[List[ToolDefinition]] = None,
    on_image: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    web_search=False,
    usage: Optional[UsageMetadata] = None,
) -> AsyncIterator[str]:
    logger.debug(f"messages: {messages}")

    api_key = os.environ["GEMINI_API_KEY"]
    if not api_key:
        raise Exception("GEMINI_API_KEY must be provided")

    # https://ai.google.dev/api/generate-content#method:-models.streamGenerateContent
    endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    contents = []
    tool_name_by_id = _build_tool_name_by_id(messages)
    for message in messages:
        parts = _message_to_parts(message, tool_name_by_id)
        assert len(parts) > 0
        contents.append({"role": _to_gemini_role(message["role"]), "parts": parts})

    if not contents:
        contents = [{"parts": [{"text": ""}]}]

    payload: Dict[str, Any] = {
        "contents": contents,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
        ],
    }

    gemini_tools = _to_gemini_tools(tools=tools, web_search=web_search)
    if gemini_tools:
        payload["tools"] = gemini_tools

    if system_prompt:
        payload["system_instruction"] = {
            "role": "system",
            "parts": [{"text": system_prompt}],
        }

    logger.debug(f"payload: {payload}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint_url,
            headers=headers,
            json=payload,
        ) as response:
            await check_for_status(response)

            async for line in iter_lines(response.content):
                line = line.strip()
                if not line.startswith(b"data: "):
                    continue

                data = json.loads(line[6:].decode("utf-8"))
                logger.debug(f"data: {data}")

                if "usageMetadata" in data:
                    usage_metadata = data["usageMetadata"]
                    if usage:
                        usage.total_tokens = usage_metadata["totalTokenCount"]
                        usage.input_tokens = usage_metadata["promptTokenCount"]
                        usage.output_tokens = usage_metadata["candidatesTokenCount"]

                for candidate in data.get("candidates", []):
                    finish_reason = candidate.get("finishReason")
                    if finish_reason:
                        if finish_reason != "STOP":
                            finish_message = candidate["finishMessage"]
                            raise Exception(
                                f"Unexpected finish reason: {finish_message}"
                            )

                    content = candidate["content"]
                    parts = content["parts"]
                    for part in parts:
                        inline_data = part.get("inlineData")
                        if not inline_data:
                            inline_data = part.get("inline_data")
                        if inline_data:
                            mime_type = inline_data.get("mimeType")
                            base64_data = inline_data.get("data")
                            if mime_type and base64_data:
                                image_url = f"data:{mime_type};base64,{base64_data}"
                                if on_image:
                                    on_image(image_url)
                                out_message.setdefault("image_urls", []).append(
                                    image_url
                                )

                        function_call = part.get("functionCall")
                        if function_call:
                            tool_use = ToolUse(
                                tool_name=function_call["name"],
                                args=function_call.get("args", {}),
                                tool_use_id=str(uuid.uuid4()),
                            )
                            if part.get("thoughtSignature"):
                                tool_use["thoughtSignature"] = part["thoughtSignature"]

                            if on_tool_use:
                                on_tool_use(tool_use)
                            out_message.setdefault("tool_use", []).append(tool_use)

                        text = part.get("text")
                        if text:
                            yield text
                            out_message["text"] += text
