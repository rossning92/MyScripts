from typing import List, Literal, NotRequired, TypedDict

from ai.tool_use import ToolResult, ToolUse


class Message(TypedDict):
    role: Literal["user", "assistant"]
    text: str
    timestamp: float
    image_file: NotRequired[str]
    tool_use: NotRequired[List[ToolUse]]
    tool_result: NotRequired[List[ToolResult]]
