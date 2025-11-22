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
import ai.openai_compatible.chat
from ai.message import Message
from ai.tool_use import ToolResult, ToolUse
from utils.textutil import truncate_text


def get_context_text(context: str) -> str:
    content = truncate_text(context)
    return f"► context: “{content}”"


def get_tool_result_text(tool_result: ToolResult) -> str:
    content = truncate_text(tool_result["content"])
    return f"► tool_result: {content}"


def get_tool_use_text(tool_use: ToolUse) -> str:
    tool_name = tool_use["tool_name"]
    args = truncate_text(str(tool_use["args"]))
    return f"► tool_use: {tool_name}: {args}"


def get_reasoning_text(text: str) -> str:
    text = truncate_text(text)
    return f"► reasoning: {text}"


async def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    on_reasoning: Optional[Callable[[str], None]] = None,
    web_search: bool = False,
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
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise Exception("OPENROUTER_API_KEY is not provided")

        if "(reasoning)" in model:
            model = model.replace("(reasoning)", "")
            extra_payload = {"extra_body": {"reasoning": {"enabled": True}}}
        else:
            extra_payload = None

        return ai.openai_compatible.chat.complete_chat(
            endpoint_url="https://openrouter.ai/api/v1/chat/completions",
            api_key=openrouter_api_key,
            messages=messages,
            model=model[len(openrouter_prefix) :],
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
            on_reasoning=on_reasoning,
            extra_payload=extra_payload,
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
