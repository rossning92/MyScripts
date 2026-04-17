import inspect
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NotRequired,
    TypedDict,
    get_type_hints,
)

from utils.jsonschema import JSONSchema


class ToolUse(TypedDict):
    tool_name: str
    args: Dict[str, Any]
    tool_use_id: str

    # Gemini model may return a thought signature, e.g. { "role": "model", "parts": [{ "functionCall": {...}, "thoughtSignature": "..." }] }
    thoughtSignature: NotRequired[str]


class ToolResult(TypedDict):
    tool_use_id: str
    content: str
    image_urls: NotRequired[List[str]]


@dataclass
class ToolParam:
    name: str
    type: JSONSchema
    description: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParam]
    required: List[str]


def _find_xml_strings(tags: List[str], s: str) -> List[str]:
    tag_patt = "(?:" + "|".join([re.escape(tag) for tag in tags]) + ")"
    return re.findall(rf"<{tag_patt}>[\S\s]*?</{tag_patt}>", s, flags=re.MULTILINE)


def _parse_xml_string_for_tool(s: str) -> ToolUse:
    match = re.match(r"^\s*<([a-z_]+)>([\d\D]*?)</\1>\s*$", s)
    if match is None:
        raise Exception()
    tool_name = match.group(1)
    params_xml_str = match.group(2)

    param_patt = re.compile(r"^\s*<([a-z_]+)>[\r\n]*([\d\D]*?)[\r\n]*</\1>\s*")
    params: Dict[str, str] = {}
    while True:
        match = re.match(param_patt, params_xml_str)
        if match:
            name = match.group(1)
            if name in params:
                raise ValueError(f"Duplicate parameter detected: {name}")
            value = match.group(2)
            params[name] = (
                value.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            )
            end = match.span()[1]
            params_xml_str = params_xml_str[end:]
        else:
            break
    return ToolUse(tool_name=tool_name, args=params, tool_use_id=str(uuid.uuid4()))


def parse_text_for_tool_use(
    text: str,
    tools: List[ToolDefinition],
) -> Iterable[ToolUse]:
    xml_strings = _find_xml_strings([t.name for t in tools], text)
    for xml_string in xml_strings:
        yield _parse_xml_string_for_tool(xml_string)


def get_tool_use_prompt(tools: List[ToolDefinition]) -> str:
    # Load prompt template from file
    prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "tool_use.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    prompt = prompt_file.read_text(encoding="utf-8").strip() + "\n\n"

    for tool in tools:
        prompt += f"### {tool.name}\n\n"
        if tool.description:
            prompt += f"{tool.description.strip()}\n"
        prompt += "Usage:\n"
        prompt += f"<{tool.name}>\n"
        for param in tool.parameters:
            prompt += f"<{param.name}>...</{param.name}>\n"
        prompt += f"</{tool.name}>\n\n"

    logging.debug(prompt)
    return prompt


def python_type_to_tool_param_type(t: int | float | bool | str) -> JSONSchema:
    if t is int:
        return {"type": "integer"}
    elif t is float:
        return {"type": "number"}
    elif t is bool:
        return {"type": "boolean"}
    elif t is str:
        return {"type": "string"}
    else:
        raise ValueError(f"Unsupported type: {t}")


def function_to_tool_definition(func: Callable[..., Any]) -> ToolDefinition:
    """Convert a function to a tool definition."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    type_hints = get_type_hints(func)

    properties: List[ToolParam] = []
    required = []

    for name, param in sig.parameters.items():
        if name not in type_hints:
            raise ValueError(f"Missing type hint for {func.__name__} param: {name}")
        param_type = type_hints[name]
        properties.append(
            ToolParam(
                name=name,
                type=python_type_to_tool_param_type(param_type),
                description=f"Parameter {name}",
            )
        )

        if param.default is inspect.Parameter.empty:
            required.append(name)

    return ToolDefinition(
        name=func.__name__, description=doc, parameters=properties, required=required
    )
