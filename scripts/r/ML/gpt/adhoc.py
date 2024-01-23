import argparse
import json
import os
from typing import List

from ML.gpt.chatgpt import ChatMenu
from utils.menu.textinput import TextInput

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str)
    args = parser.parse_args()

    prompt_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prompts.json"
    )

    prompts: List[str] = []
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompts += json.load(f)

    if os.environ.get("CUSTOM_PROMPT_FILE", ""):
        custom_prompt_file = os.environ["CUSTOM_PROMPT_FILE"]
        with open(custom_prompt_file, "r", encoding="utf-8") as f:
            prompts += json.load(f)

    prompt_text = TextInput(items=prompts).request_input()

    if prompt_text:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input
        chat = ChatMenu(
            first_message=prompt_text + ":\n---\n" + input_text, model="gpt-4"
        )
        chat.exec()
