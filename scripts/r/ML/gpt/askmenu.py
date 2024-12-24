import argparse
import glob
import os
from typing import Dict, List, Optional

from ML.gpt.chatmenu import ChatMenu
from utils.historymanager import HistoryManager
from utils.logger import setup_logger
from utils.menu import Menu
from utils.menu.inputmenu import InputMenu
from utils.template import render_template


def _get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


class _Prompt:
    def __init__(
        self,
        path: str,
    ) -> None:
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.path = path

    def __str__(self) -> str:
        return self.name

    def load_prompt(self) -> str:
        with open(self.path, "r", encoding="utf-8") as file:
            return file.read()


def _get_context(s: str) -> str:
    if os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return s


def load_prompts_from_dir(prompt_dir: str) -> List[_Prompt]:
    prompts: List[_Prompt] = []

    if not os.path.isdir(prompt_dir):
        raise ValueError(f"The directory {prompt_dir} does not exist.")

    files = glob.glob(os.path.join(prompt_dir, "**", "*.md"), recursive=True)
    for file_path in files:
        if os.path.isfile(file_path):
            prompts.append(_Prompt(path=file_path))

    return prompts


def _get_prompt_dir() -> str:
    prompt_dir = os.environ.get("PROMPT_DIR")
    if prompt_dir:
        return prompt_dir

    prompt_dir = os.path.join(_get_script_dir(), "prompts")
    return prompt_dir


class AskMenu(ChatMenu):
    def __init__(self, context: str, prompt_file=None, **kwargs):
        self.__context = _get_context(context)
        self.__history_manager = HistoryManager(
            save_dir=_get_prompt_dir(), prefix="temp-", ext=".md"
        )
        self.__prompt_file: Optional[str] = prompt_file
        super().__init__(**kwargs)

    def on_created(self):
        if not self.__prompt_file:
            prompts = load_prompts_from_dir(_get_prompt_dir())
            menu = Menu(items=prompts, wrap_text=True, history="chatmenu_adhoc")
            menu.exec()

            selected = menu.get_selected_item()
            if selected is not None:
                prompt = selected.load_prompt()
                self.__ask_question(prompt)
            else:
                self.__prompt_file = prompt_file = self.__history_manager.get_new_file()
                prompt = menu.get_input()
                if prompt:
                    with open(prompt_file, "w", encoding="utf-8") as f:
                        f.write(prompt)
        else:
            with open(self.__prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()

        if prompt:
            context: Dict[str, str] = {}
            while True:
                undefined_names: List[str] = []
                final_prompt = render_template(
                    template=prompt,
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

            self.__ask_question(final_prompt)

    def __ask_question(self, question: str):
        self.clear_messages()
        super().send_message(question + ":\n---\n" + self.__context)


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", nargs="?", type=str)
    parser.add_argument("-p", "--prompt", default=None, type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-x",
        "--copy-result-and-exit",
        action="store_true",
        help="Copy the last message and then exit",
    )

    args = parser.parse_args()

    if args.verbose:
        setup_logger()

    chat = AskMenu(
        context=args.context,
        prompt_file=args.prompt,
        copy_result_and_exit=args.copy_result_and_exit,
    )
    chat.exec()


if __name__ == "__main__":
    _main()
