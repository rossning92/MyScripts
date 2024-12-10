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
    ai_provider = os.getenv("API_PROVIDER", "openai").lower()
    if ai_provider == "anthropic":
        return ai.anthropic.complete_chat.complete_chat(message)
    else:
        return ai.openai.complete_chat.complete_chat(message, model=model)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str)
    args = parser.parse_args()

    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input

    for chunk in complete_chat(input_text):
        print(chunk, end="")
