import argparse
import glob
import logging
import os
import sys
from typing import List, Optional

from ai.openai.complete_chat import chat_completion
from ML.gpt.chatmenu import ChatMenu
from utils.logger import setup_logger
from utils.menu import Menu


def _get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


class _Prompt:
    def __init__(
        self, prompt: str, name: Optional[str] = None, hotkey: Optional[str] = None
    ) -> None:
        self.name = name
        self.prompt = prompt
        self.hotkey = hotkey

    def __str__(self) -> str:
        return self.name if self.name else self.prompt


def get_input(s: str) -> str:
    if os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return s


def load_prompts_from_dir(prompt_dir: str) -> List[_Prompt]:
    prompts: List[_Prompt] = []

    if not os.path.isdir(prompt_dir):
        raise ValueError(f"The directory {prompt_dir} does not exist.")

    files = glob.glob(os.path.join(prompt_dir, "*.md"))
    for file_path in files:
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                prompt = file.read()
                filename = os.path.basename(file_path)
                prompts.append(
                    _Prompt(prompt=prompt, name=os.path.splitext(filename)[0])
                )

    return prompts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=str)
    parser.add_argument("-p", "--prompt", default=None, type=str)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        setup_logger()

    # Read prompt
    if args.prompt is not None:
        prompt = args.prompt
        if not os.path.isabs(prompt):
            if os.environ.get("PROMPT_DIR"):
                prompt_file = os.path.join(os.environ["PROMPT_DIR"], prompt)
                if os.path.isfile(prompt_file):
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        prompt = f.read()
    else:
        prompts: List[_Prompt] = []
        prompt_dir = os.path.join(_get_script_dir(), "prompts")
        assert os.path.isdir(prompt_dir)
        prompts = load_prompts_from_dir(prompt_dir=prompt_dir)
        if os.environ.get("PROMPT_DIR"):
            prompts += load_prompts_from_dir(os.environ["PROMPT_DIR"])

        menu = Menu(items=prompts, wrap_text=True, history="chatmenu_adhoc")
        menu.exec()

        selected_item = menu.get_selected_item()
        if selected_item is not None:
            prompt = selected_item.prompt
        else:
            prompt = menu.get_input()
    if not prompt:
        raise Exception("Prompt must not be empty.")

    # Read input text.
    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
        message = prompt + ":\n---\n" + input_text
        logging.debug(message)
        for chunk in chat_completion([{"role": "user", "content": message}]):
            print(chunk, end="")

    else:
        input_text = get_input(args.input)
        message = prompt + ":\n---\n" + input_text
        logging.debug(message)
        chat = ChatMenu(message=message)
        chat.exec()
