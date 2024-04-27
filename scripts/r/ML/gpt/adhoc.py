import argparse
import json
import os
from typing import List, Optional

from ML.gpt.chatgpt import ChatMenu
from utils.menu import Menu


class _Prompt:
    def __init__(
        self, prompt: str, name: Optional[str] = None, hotkey: Optional[str] = None
    ) -> None:
        self.name = name
        self.prompt = prompt
        self.hotkey = hotkey

    def __str__(self) -> str:
        return self.name if self.name else self.prompt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str)
    args = parser.parse_args()

    prompt_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prompts.json"
    )

    data = []
    with open(prompt_file, "r", encoding="utf-8") as f:
        data.extend(json.load(f))
    if os.environ.get("CUSTOM_PROMPT_FILE", ""):
        custom_prompt_file = os.environ["CUSTOM_PROMPT_FILE"]
        with open(custom_prompt_file, "r", encoding="utf-8") as f:
            data.extend(json.load(f))

    prompts: List[_Prompt] = []
    for item in data:
        prompts.append(
            _Prompt(
                prompt=item["prompt"],
                name=item["name"] if "name" in item else None,
                hotkey=item["hotkey"] if "hotkey" in item else None,
            )
        )

    menu = Menu(items=prompts, wrap_text=True)
    menu.exec()

    selected_item = menu.get_selected_item()
    if selected_item is not None:
        prompt = selected_item.prompt
    else:
        prompt = menu.get_input()

    if prompt:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input
        chat = ChatMenu(first_message=prompt + ":\n---\n" + input_text, model="gpt-4")
        chat.exec()
