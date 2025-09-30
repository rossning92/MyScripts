import argparse
import os
import sys
from datetime import datetime
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Optional,
)

import ai.anthropic.chat
import ai.openai.chat
from ai.message import Message
from ai.tool_use import ToolResult, ToolUse
from utils.textutil import truncate_text


def get_tool_result_text(tool_result: ToolResult) -> str:
    content = truncate_text(tool_result["content"])
    return f"❉ tool_result: {content}"


def get_tool_use_text(tool_use: ToolUse) -> str:
    tool_name = tool_use["tool_name"]
    args = truncate_text(str(tool_use["args"]))
    return f"❉ tool_use: {tool_name}: {args}"


def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    web_search: bool = False,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        return ai.anthropic.chat.complete_chat(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use_args_delta=on_tool_use_args_delta,
            on_tool_use=on_tool_use,
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
