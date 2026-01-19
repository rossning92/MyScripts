import os
from typing import AsyncIterator, Callable, Dict, List, Optional

import ai.openai_compatible.chat
from ai.message import Message
from ai.tool_use import ToolDefinition, ToolUse
from ai.usagemetadata import UsageMetadata


async def complete_chat(
    messages: List[Message],
    out_message: Message,
    model: str,
    system_prompt: Optional[str] = None,
    tools: Optional[List[ToolDefinition]] = None,
    on_image: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    on_reasoning: Optional[Callable[[str], None]] = None,
    usage: Optional[UsageMetadata] = None,
) -> AsyncIterator[str]:
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise Exception("OPENROUTER_API_KEY is not provided")

    extra_payload: Dict = {}
    if "(reasoning)" in model:
        model = model.replace("(reasoning)", "")
        extra_payload.setdefault("extra_body", {})["reasoning"] = {"enabled": True}

    if "image" in model:
        extra_payload.setdefault("extra_body", {})["modalities"] = ["image", "text"]

    return ai.openai_compatible.chat.complete_chat(
        messages=messages,
        out_message=out_message,
        endpoint_url="https://openrouter.ai/api/v1/chat/completions",
        api_key=openrouter_api_key,
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        on_image=on_image,
        on_tool_use=on_tool_use,
        on_reasoning=on_reasoning,
        extra_payload=extra_payload,
        usage=usage,
    )
