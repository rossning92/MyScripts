import json
import logging
import os
from base64 import b64decode
from typing import AsyncIterator, Callable, List, Optional

import aiohttp
from ai.message import Message
from utils.http import check_for_status
from utils.imagedataurl import parse_image_data_url


async def complete_chat(
    messages: List[Message],
    model: str,
    system_prompt: Optional[str] = None,
    on_image: Optional[Callable[[str], None]] = None,
    out_message: Optional[Message] = None,
) -> AsyncIterator[str]:
    logging.debug(f"messages: {messages}")

    api_key = os.environ["GEMINI_API_KEY"]
    if not api_key:
        raise Exception("GEMINI_API_KEY must be provided")

    endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    contents = []
    for message in messages:
        parts = _message_to_parts(message)
        assert len(parts) > 0
        contents.append({"role": message["role"], "parts": parts})

    if not contents:
        contents = [{"parts": [{"text": ""}]}]

    safety_settings = "W3siY2F0ZWdvcnkiOiJIQVJNX0NBVEVHT1JZX0hBUkFTU01FTlQiLCJ0aHJlc2hvbGQiOiJPRkYifSx7ImNhdGVnb3J5IjoiSEFSTV9DQVRFR09SWV9IQVRFX1NQRUVDSCIsInRocmVzaG9sZCI6Ik9GRiJ9LHsiY2F0ZWdvcnkiOiJIQVJNX0NBVEVHT1JZX1NFWFVBTExZX0VYUExJQ0lUIiwidGhyZXNob2xkIjoiT0ZGIn0seyJjYXRlZ29yeSI6IkhBUk1fQ0FURUdPUllfREFOR0VST1VTX0NPTlRFTlQiLCJ0aHJlc2hvbGQiOiJPRkYifV0="
    payload = {
        "contents": contents,
        "safetySettings": json.loads(b64decode(safety_settings)),
    }

    if system_prompt:
        payload["system_instruction"] = {
            "role": "system",
            "parts": [{"text": system_prompt}],
        }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint_url,
            headers=headers,
            json=payload,
        ) as response:
            await check_for_status(response)

            data = await response.json()
            logging.debug(f"data: {data}")

            for candidate in data["candidates"]:
                finish_reason = candidate.get("finishReason")
                if finish_reason != "STOP":
                    finish_message = candidate["finishMessage"]
                    raise Exception(f"Unexpected finish reason: {finish_message}")

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
                            if out_message:
                                out_message.setdefault("image_urls", []).append(
                                    image_url
                                )

                    text = part.get("text")
                    if text:
                        yield text
                        if out_message:
                            out_message["text"] += text


def _message_to_parts(message: Message):
    parts = []

    text = message.get("text")
    if text:
        parts.append({"text": text})

    image_urls = message.get("image_urls") or []
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
