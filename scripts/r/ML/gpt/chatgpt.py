import argparse
import builtins
import os
import sys
from typing import Dict, Iterator, List, Optional

from _shutil import load_json, pause, save_json
from _term import clear_terminal
from ai.openai.chat_completion import chat_completion
from utils.clip import set_clip
from utils.menu import Menu
from utils.menu.actionmenu import ActionMenu
from utils.printc import printc


class Chat:
    def __init__(self, stream_mode: bool = True) -> None:
        self.stream_mode = stream_mode
        self.messages: List[Dict[str, str]] = []

        # https://platform.openai.com/account/api-keys

        self.start_new_chat()

    def _send(self, message: str) -> Iterator[str]:
        self.messages.append({"role": "user", "content": message})
        content = ""
        for chunk in chat_completion(self.messages):
            content += chunk
            yield chunk
        self.messages.append({"role": "assistant", "content": content})

    def send(self, message: str) -> str:
        printc("> ", end="", color="yellow")
        response = ""
        for chunk in self._send(message):
            response += chunk
            printc(chunk, end="", color="yellow")
        print()
        return response

    def save_chat(self, file: str):
        save_json(file, {"messages": self.messages})

    def load_chat(self, file: str):
        if os.path.isfile(file):
            data = load_json(file)
            self.messages = data["messages"]

            for message in self.messages:
                if message["role"] != "system":
                    if message["role"] == "assistant":
                        printc(f"> {message['content']}", color="yellow")
                    else:
                        print(f"> {message['content']}")

    def start_new_chat(self):
        self.messages.clear()
        self.messages.append(
            {"role": "system", "content": "You are a helpful assistant."}
        )
        clear_terminal()

    def copy_last_message(self):
        if len(self.messages) > 0:
            set_clip(self.messages[-1]["content"])


def complete_chat(
    *,
    input: str,
    prompt_text: Optional[str] = None,
    copy_to_clipboard: bool = False,
    pause: bool = False,
    _pause=pause,
):
    if os.path.isfile(input):
        with open(input, "r", encoding="utf-8") as f:
            input = f.read()

    if prompt_text:
        input = prompt_text + "\n\n\n" + input

    full_response = ""
    chat = Chat()
    for chunk in chat._send(input):
        full_response += chunk
        print(chunk, end="")

    if pause:
        print("\n")
        _pause()

    if copy_to_clipboard:
        set_clip(full_response)

    return full_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?", default=None)
    parser.add_argument("-c", "--copy-to-clipboard", action="store_true", default=False)
    parser.add_argument("-p", "--load-prompt-file", action="store_true", default=False)
    parser.add_argument(
        "--adhoc",
        default=None,
        help="Ad-hoc prompt text",
        type=str,
    )
    parser.add_argument(
        "--pause", help="Pause after completion.", action="store_true", default=False
    )
    args = parser.parse_args()

    # If input is provided
    if args.input:
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input = f.read()

        else:
            input = args.input

        # Specify custom ad-hoc prompt if any
        if args.adhoc:
            prompt_text = args.adhoc

        elif args.load_prompt_file:
            prompt_file = os.path.join(os.environ["MY_DATA_DIR"], "custom_prompts.json")
            if os.path.exists(prompt_file):
                options = load_json(prompt_file)
                idx = Menu(options, history="custom_prompts").exec()
                if idx < 0:
                    sys.exit(0)
                prompt_text = options[idx]
            else:
                prompt_text = None
        else:
            prompt_text = None

        complete_chat(
            input=input,
            prompt_text=prompt_text,
            copy_to_clipboard=args.copy_to_clipboard,
            pause=args.pause,
        )

    else:  # empty
        start_conversation(
            chat_history=os.path.join(
                os.environ["MY_DATA_DIR"], "chatgpt_start_conversation.json"
            )
        )


class _Menu(ActionMenu):
    def __init__(self, chat: Chat):
        super().__init__()
        self.__chat = chat

    @ActionMenu.action()
    def clear(self):
        self.__chat.start_new_chat()

    @ActionMenu.action()
    def copy_last_message(self):
        self.__chat.copy_last_message()


def start_conversation(
    *,
    input: Optional[str] = None,
    prompt_text: Optional[str] = None,
    chat_history: Optional[str] = None,
):
    chat = Chat()

    # Load existing chat
    if chat_history:
        chat.load_chat(chat_history)

    if input and os.path.isfile(input):
        with open(input, "r", encoding="utf-8") as f:
            input = f.read()

    if input and prompt_text:
        input = prompt_text + "\n\n\n" + input
        chat.send(input)

    try:
        while True:
            message = builtins.input("> ")
            if message == "":
                _Menu(chat=chat).exec()

            else:
                chat.send(message)

            if chat_history:
                chat.save_chat(chat_history)

    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    main()
