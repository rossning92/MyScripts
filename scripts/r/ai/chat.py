import argparse
import base64
import os
import sys
from typing import Any, Callable, Dict, Iterator, List, Optional

from ai.tool_use import ToolResult, ToolUse


def complete_chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Callable[..., Any]]] = None,
    on_tool_use: Optional[Callable[[ToolUse], None]] = None,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        import ai.anthropic.chat

        return ai.anthropic.chat.complete_chat(
            messages,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            on_tool_use=on_tool_use,
        )
    else:
        import ai.openai.chat

        return ai.openai.chat.complete_chat(
            messages,
            model=model,
            system_prompt=system_prompt,
        )


def _encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_user_message(
    text: str,
    image_file: Optional[str] = None,
    tool_results: Optional[List[ToolResult]] = None,
) -> Dict[str, Any]:
    content = []
    if tool_results:
        content += [
            {
                "type": "tool_result",
                "tool_use_id": tr.tool_use_id,
                "content": tr.content,
            }
            for tr in tool_results
        ]
    if image_file:
        content += [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{_encode_image_base64(image_file)}"
                },
            },
        ]
    if text:
        content += [{"type": "text", "text": text}]

    if len(content) == 0:
        raise ValueError(
            "At least one text, image file, or tool results must be provided."
        )
    if len(content) == 1 and text:
        return {"role": "user", "content": text}
    else:
        return {"role": "user", "content": content}


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
    for chunk in complete_chat([{"role": "user", "content": input_text}]):
        output += chunk
        if not args.quiet:
            print(chunk, end="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
