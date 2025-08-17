import inspect
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class ToolUse:
    tool_name: str
    args: Dict[str, Any]
    tool_use_id: str = ""


@dataclass
class ToolResult:
    tool_use_id: str
    content: str


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
    return ToolUse(
        tool_name=tool_name,
        args=params,
    )


def parse_text_for_tool_use(
    text: str,
    tools: List[Callable],
) -> Iterable[ToolUse]:
    xml_strings = _find_xml_strings([t.__name__ for t in tools], text)
    for i, xml_string in enumerate(xml_strings):
        # Parse the XML string for the tool usage into valid Python code to be executed.
        yield _parse_xml_string_for_tool(xml_string)


def get_tool_use_prompt(tools: List[Callable]):
    prompt = """# Tool Use

You can use the available tools to complete the user's task.

IMPORTANT:
- You MUST wait for the actual tool result before proceeding.

## Formatting

You MUST use the tools in the following format as part of your message. I will reply in the next message with the result of the tool use.
Tool use is formatted using XML-style tags.
The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags.
Do not escape any characters in parameters, such as `<`, `>`, and `&`, in XML tags. Do not wrap parameters in `<![CDATA[` and `]]>`.
You can directly put multiline text in XML tags.
Always adhere to this format for the tool use to ensure proper parsing and execution. Here's the structure:

<tool_name>
<param1>...</param1>
<param2>...</param2>
...
</tool_name>

## Tools

"""

    for tool in tools:
        prompt += f"### {tool.__name__}\n\n"
        if tool.__doc__:
            prompt += f"{tool.__doc__.strip()}\n"
        prompt += "Usage:\n"
        prompt += f"<{tool.__name__}>\n"
        for param in inspect.signature(tool).parameters.values():
            prompt += f"<{param.name}>...</{param.name}>\n"
        prompt += f"</{tool.__name__}>\n\n"

    logging.debug(prompt)
    return prompt
