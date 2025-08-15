import argparse
import os
import sys
from typing import Any, Dict, Iterator, List, Optional

import ai.anthropic.chat
import ai.openai.chat


def complete_chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        return ai.anthropic.chat.complete_chat(
            messages,
            model=model,
            system_prompt=system_prompt,
        )
    else:
        return ai.openai.chat.complete_chat(
            messages,
            model=model,
            system_prompt=system_prompt,
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
    for chunk in complete_chat([{"role": "user", "content": input_text}]):
        output += chunk
        if not args.quiet:
            print(chunk, end="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
