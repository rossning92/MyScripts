import argparse
import os
import sys
from typing import Any, Dict, Iterator, List, Optional, Union

import ai.anthropic.complete_chat
import ai.openai.complete_chat


def complete_chat(
    message: Union[str, List[Dict[str, Any]]],
    model: Optional[str] = None,
) -> Iterator[str]:
    if model and model.startswith("claude"):
        return ai.anthropic.complete_chat.complete_chat(message)
    else:
        return ai.openai.complete_chat.complete_chat(message, model=model)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str)
    parser.add_argument("-o", "--output", type=str)
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
    for chunk in complete_chat(input_text):
        output += chunk
        print(chunk, end="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
