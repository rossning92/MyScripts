import argparse
import base64
import inspect
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
    get_type_hints,
)

from ai.tool_use import ToolResult, ToolUse


class Message(TypedDict):
    role: Literal["user", "assistant"]
    text: str
    timestamp: float
    image_file: NotRequired[str]
    tool_use: NotRequired[List[ToolUse]]
    tool_result: NotRequired[List[ToolResult]]


def message_to_str(message: Message) -> str:
    out = []
    if message["text"]:
        out.append(message["text"])
    image_file = message.get("image_file", None)
    if image_file:
        out.append(f"* Image: {image_file}")
    for tool_use in message.get("tool_use", []):
        tool_name = tool_use["tool_name"]
        out.append(f"* Running tool: {tool_name}")
    for tool_result in message.get("tool_result", []):
        first_line = tool_result["content"].splitlines()[0]
        out.append(f'* Tool result: "{first_line} ..."')
    return "\n".join(out)


def _encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _to_openai_message_content(message: Message) -> List[Dict[str, Any]]:
    content = [
        {
            "type": "input_text" if message["role"] == "user" else "output_text",
            "text": message["text"],
        }
    ]
    if "image_file" in message:
        content.append(
            {
                "type": "input_image",
                "image_url": "data:image/jpeg;base64,{}".format(
                    _encode_image_base64(message["image_file"])
                ),
            }
        )
    return content


def _to_claude_message_content(message: Message) -> List[Dict[str, Any]]:
    content = []

    # Add text content
    if message["text"]:
        content.append({"type": "text", "text": message["text"]})

    # Add tool uses
    tool_uses = message.get("tool_use", [])
    for tool_use in tool_uses:
        content.append(
            {
                "type": "tool_use",
                "name": tool_use["tool_name"],
                "id": tool_use["tool_use_id"],
                "input": tool_use["args"],
            }
        )

    # Add tool results
    tool_results = message.get("tool_result", [])
    for tool_result in tool_results:
        content.append(
            {
                "type": "tool_result",
                "tool_use_id": tool_result["tool_use_id"],
                "content": tool_result["content"],
            }
        )

    return content


def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        import ai.anthropic.chat

        return ai.anthropic.chat.complete_chat(
            messages=[
                {
                    "role": message["role"],
                    "content": _to_claude_message_content(message),
                }
                for message in messages
            ],
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use=on_tool_use,
        )
    else:
        import ai.openai.chat

        return ai.openai.chat.complete_chat(
            messages=[
                {
                    "role": message["role"],
                    "content": _to_openai_message_content(message),
                }
                for message in messages
            ],
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
        )


@dataclass
class ToolParam:
    name: str
    type: Literal["integer", "number", "boolean", "string"]
    description: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParam]
    required: List[str]


def function_to_tool_definition(func: Callable[..., Any]) -> ToolDefinition:
    """Convert a function to a tool definition."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    type_hints = get_type_hints(func)

    properties: List[ToolParam] = []
    required = []

    for name, param in sig.parameters.items():
        param_type = type_hints.get(name, None)
        type_str: Literal["integer", "number", "boolean", "string"] = "string"
        if param_type is not None:
            if issubclass(param_type, int):
                type_str = "integer"
            elif issubclass(param_type, float):
                type_str = "number"
            elif issubclass(param_type, bool):
                type_str = "boolean"

        properties.append(
            ToolParam(name=name, type=type_str, description=f"Parameter {name}")
        )

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return ToolDefinition(
        name=func.__name__, description=doc, parameters=properties, required=required
    )


def get_text_content(message: Dict[str, Any]) -> str:
    content = message["content"]
    if isinstance(content, str):
        return content
    else:
        assert isinstance(content, list)
        for part in content:
            assert isinstance(part, dict), "Content must a list of dicts"
            if part["type"] == "text":
                return part["text"]
        return ""


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
