from typing import (
    AsyncIterator,
    Callable,
    List,
    Optional,
)

import ai.anthropic.chat
import ai.gemini.chat
import ai.openai.chat
import ai.openai_compatible.chat
import ai.openrouter.chat
from ai.message import Message
from ai.tool_use import ToolDefinition, ToolResult, ToolUse
from utils.textutil import truncate_text


def get_image_url_text(image_url: str) -> str:
    return "► image: {}".format(image_url[:32] + "...")


def get_context_text(context: str) -> str:
    return "► context: “{}”".format(truncate_text(context))


def get_tool_result_text(tool_result: ToolResult) -> str:
    return "► tool_result: {}".format(truncate_text(tool_result["content"]))


def get_tool_use_text(tool_use: ToolUse) -> str:
    tool_name = tool_use["tool_name"]
    args = truncate_text(str(tool_use["args"]))
    return "► tool_use: {}: {}".format(tool_name, args)


def get_reasoning_text(text: str) -> str:
    return "► reasoning: {}".format(truncate_text(text))


async def complete_chat(
    messages: List[Message],
    out_message: Message,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[ToolDefinition]] = None,
    on_image: Optional[Callable[[str], None]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    on_reasoning: Optional[Callable[[str], None]] = None,
    web_search=False,
) -> AsyncIterator[str]:
    OPENROUTER_PREFIX = "openrouter:"
    LLAMA_CPP_PREFIX = "llama.cpp:"

    if model and model.startswith("claude"):
        return ai.anthropic.chat.complete_chat(
            messages=messages,
            out_message=out_message,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use_args_delta=on_tool_use_args_delta,
            on_tool_use=on_tool_use,
        )
    elif model and model.startswith(OPENROUTER_PREFIX):
        model = model[len(OPENROUTER_PREFIX) :]

        return await ai.openrouter.chat.complete_chat(
            messages=messages,
            out_message=out_message,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_image=on_image,
            on_tool_use=on_tool_use,
            on_reasoning=on_reasoning,
        )
    elif model and model.startswith("gemini"):
        return ai.gemini.chat.complete_chat(
            messages=messages,
            out_message=out_message,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_image=on_image,
            on_tool_use=on_tool_use,
        )
    elif model and model.startswith(LLAMA_CPP_PREFIX):
        model = model[len("llama.cpp:") :]
        return ai.openai_compatible.chat.complete_chat(
            endpoint_url="http://127.0.0.1:8080/v1/chat/completions",
            api_key="dummy-key",
            messages=messages,
            out_message=out_message,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
        )
    else:
        return ai.openai.chat.complete_chat(
            messages=messages,
            out_message=out_message,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use=on_tool_use,
            web_search=web_search,
        )
