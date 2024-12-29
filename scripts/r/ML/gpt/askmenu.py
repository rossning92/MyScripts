import argparse
import os
from typing import Dict, List, Optional

from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
from utils.logger import setup_logger
from utils.menu.filemenu import FileMenu
from utils.menu.inputmenu import InputMenu
from utils.template import render_template


def _get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _get_context(s: str) -> str:
    if os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return s


def _get_prompt_dir() -> str:
    prompt_dir = os.environ.get("PROMPT_DIR")
    if prompt_dir:
        return prompt_dir

    prompt_dir = os.path.join(_get_script_dir(), "prompts")
    return prompt_dir


class AskMenu(ChatMenu):
    def __init__(self, context: str, prompt_file=None, **kwargs):
        self.__context = _get_context(context)
        if not self.__context:
            raise Exception("Context must not be empty")

        self.__prompt_file: Optional[str] = prompt_file
        self.__prompt: str = ""

        super().__init__(
            prompt=f"context: {self.__context.splitlines()[0][:50]}\na", **kwargs
        )

        self.add_command(self.__edit_prompt, hotkey="alt+p")

    def __edit_prompt(self):
        self.__prompt = self.call_func_without_curses(lambda: edit_text(self.__prompt))
        if self.__prompt_file:
            with open(self.__prompt_file, "w", encoding="utf-8") as f:
                f.write(self.__prompt)

        self.__ask_question()

    def on_created(self):
        if self.__prompt_file:
            with open(self.__prompt_file, "r", encoding="utf-8") as f:
                self.__prompt = f.read()
        else:
            menu = FileMenu(
                prompt="prompt",
                goto=_get_prompt_dir(),
                show_size=False,
                recursive=True,
                allow_cd=False,
            )
            selected = menu.select_file()
            if selected:
                with open(selected, "r", encoding="utf-8") as f:
                    self.__prompt = f.read()
                self.__prompt_file = selected
            else:
                self.__prompt = menu.get_input()

        if self.__prompt:
            self.__ask_question()

    def __ask_question(self):
        assert self.__prompt

        # Ask user to input context
        context: Dict[str, str] = {}
        while True:
            undefined_names: List[str] = []
            prompt = render_template(
                template=self.__prompt,
                context=context,
                undefined_names=undefined_names,
            )
            if len(undefined_names) > 0:
                for name in undefined_names:
                    val = InputMenu(prompt=name).request_input()
                    if val:
                        context[name] = val
            else:
                break

        # Send message
        self.clear_messages()
        super().send_message(prompt + ":\n---\n" + self.__context)


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", nargs="?", type=str)
    parser.add_argument("-p", "--prompt", default=None, type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-x",
        "--copy-and-exit",
        action="store_true",
        help="Copy the last message and then exit",
    )

    args = parser.parse_args()

    if args.verbose:
        setup_logger()

    chat = AskMenu(
        context=args.context,
        prompt_file=args.prompt,
        copy_and_exit=args.copy_and_exit,
    )
    chat.exec()


if __name__ == "__main__":
    _main()
