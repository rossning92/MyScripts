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
        out.append(f'<img src="{image_file}"/>')
    for tool_use in message.get("tool_use", []):
        out.append(str(tool_use))
    for tool_result in message.get("tool_result", []):
        out.append(str(tool_result))
    return "\n".join(out)


def complete_chat(
    messages: List[Message],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        import ai.anthropic.chat

        return ai.anthropic.chat.complete_chat(
            messages=[
                {
                    "role": message["role"],
                    "content": (
                        (
                            [{"type": "text", "text": message["text"]}]
                            if message["text"]
                            else []
                        )
                        + [
                            {
                                "type": "tool_use",
                                "name": t["tool_name"],
                                "id": t["tool_use_id"],
                                "input": t["args"],
                            }
                            for t in message.get("tool_use", [])
                        ]
                        + [
                            {
                                "type": "tool_result",
                                "tool_use_id": t["tool_use_id"],
                                "content": t["content"],
                            }
                            for t in message.get("tool_result", [])
                        ]
                    ),
                }
                for message in messages
            ],
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
        )
    else:
        import ai.openai.chat

        return ai.openai.chat.complete_chat(
            messages=[
                {"role": message["role"], "content": message["text"]}
                for message in messages
            ],
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
        )


def _encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
