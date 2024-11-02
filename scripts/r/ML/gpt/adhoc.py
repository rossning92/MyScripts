import argparse
import glob
import logging
import os
import sys
from typing import List, Optional

from ai.openai.complete_chat import complete_messages
from ML.gpt.chatmenu import ChatMenu
from utils.logger import setup_logger
from utils.menu import Menu
from utils.template import render_template


def _get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


class _Prompt:
    def __init__(
        self,
        path: str,
        hotkey: Optional[str] = None,
    ) -> None:
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.path = path
        self.hotkey = hotkey

    def __str__(self) -> str:
        return self.name

    def load_prompt(self) -> str:
        with open(self.path, "r", encoding="utf-8") as file:
            prompt = file.read()
            return render_template(template=prompt)


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
            prompts.append(_Prompt(path=file_path))

    return prompts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=str)
    parser.add_argument("-p", "--prompt", default=None, type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--copy-and-exit", action="store_true", help="Copy the last message and exit."
    )

    args = parser.parse_args()

    if args.verbose:
        setup_logger()

    # Load prompt
    if args.prompt is not None:
        if os.path.isfile(args.prompt):
            prompt = _Prompt(path=args.prompt).load_prompt()
        elif os.environ.get("PROMPT_DIR"):
            prompt_file = os.path.join(os.environ["PROMPT_DIR"], args.prompt)
            if os.path.isfile(prompt_file):
                prompt = _Prompt(path=prompt_file).load_prompt()
            else:
                prompt = args.prompt
        else:
            prompt = args.prompt
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
            prompt = selected_item.load_prompt()
        else:
            prompt = menu.get_input()

    if not prompt:
        raise Exception("Prompt must not be empty.")

    # Read input text.
    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
        message = prompt + ":\n---\n" + input_text
        logging.debug(message)
        for chunk in complete_messages([{"role": "user", "content": message}]):
            print(chunk, end="")

    else:
        input_text = get_input(args.input)
        message = prompt + ":\n---\n" + input_text
        logging.debug(message)
        chat = ChatMenu(message=message, copy_result_and_exit=args.copy_and_exit)
        chat.exec()
