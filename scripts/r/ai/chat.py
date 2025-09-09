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


def get_tool_result_text(tool_result: ToolResult) -> str:
    lines = tool_result["content"].splitlines()
    ellipsis = " ..." if len(lines) > 1 else ""
    return f"* Tool result: {lines[0]}{ellipsis}"


def get_tool_use_text(tool_use: ToolUse) -> str:
    tool_name = tool_use["tool_name"]
    return f"* Running tool: {tool_name}"


def message_to_str(message: Message) -> str:
    out = []
    if message["text"]:
        out.append(message["text"])
    image_file = message.get("image_file", None)
    if image_file:
        out.append(f"* Image: {image_file}")
    for tool_use in message.get("tool_use", []):
        out.append(get_tool_use_text(tool_use))
    for tool_result in message.get("tool_result", []):
        out.append(get_tool_result_text(tool_result))
    return "\n".join(out)


def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
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
