import argparse
import os
import sys
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Callable,
    List,
    Optional,
)

import ai.anthropic.chat
import ai.openai.chat
import ai.openrouter.chat
from ai.message import Message
from ai.tool_use import ToolResult, ToolUse
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
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_image: Optional[Callable[[str], None]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    on_reasoning: Optional[Callable[[str], None]] = None,
    web_search=False,
    out_message: Optional[Message] = None,
) -> AsyncIterator[str]:
    openrouter_prefix = "openrouter:"

    if model and model.startswith("claude"):
        return ai.anthropic.chat.complete_chat(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use_args_delta=on_tool_use_args_delta,
            on_tool_use=on_tool_use,
            out_message=out_message,
        )
    elif model and model.startswith(openrouter_prefix):
        model = model[len(openrouter_prefix) :]

        return await ai.openrouter.chat.complete_chat(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_image=on_image,
            on_tool_use=on_tool_use,
            on_reasoning=on_reasoning,
            out_message=out_message,
        )
    else:
        return ai.openai.chat.complete_chat(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use=on_tool_use,
            web_search=web_search,
            out_message=out_message,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input

    output = ""
    for chunk in complete_chat(
        [Message(role="user", text=input_text, timestamp=datetime.now().timestamp())]
    ):
        output += chunk
        if not args.quiet:
            print(chunk, end="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
