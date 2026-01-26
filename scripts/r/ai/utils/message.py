from typing import List, Literal, NotRequired, TypedDict

from ai.utils.tooluse import ToolResult, ToolUse


class Message(TypedDict):
    role: Literal["user", "assistant"]
    timestamp: float

    text: str
    context: NotRequired[List[str]]
    image_urls: NotRequired[List[str]]

    reasoning: NotRequired[List[str]]
    tool_use: NotRequired[List[ToolUse]]
    tool_result: NotRequired[List[ToolResult]]

    # Used only by openrouter
    reasoning_details: NotRequired[List[dict]]
