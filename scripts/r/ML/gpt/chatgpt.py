import argparse
import builtins
import json
import os
import sys
from typing import Dict, Iterator, List, Optional

import requests
from _shutil import load_json, pause, save_json
from _term import clear_terminal
from utils.clip import set_clip
from utils.menu import Menu

openai_api_key = os.environ["OPENAI_API_KEY"]
if not openai_api_key:
    raise Exception("OPENAI_API_KEY must be provided.")


def stream(messages: List[Dict[str, str]]) -> Iterator[str]:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "stream": True,
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    for chunk in response.iter_lines():
        if len(chunk) == 0:
            continue

        if b"DONE" in chunk:
            break

        try:
            decoded_line = json.loads(chunk.decode("utf-8").split("data: ")[1])
            token = decoded_line["choices"][0]["delta"].get("content")

            if token is not None:
                yield token

        except GeneratorExit:
            break


class ChatAPI:
    def __init__(self, stream_mode: bool = True) -> None:
        self.stream_mode = stream_mode
        self.messages: List[Dict[str, str]] = []

        # https://platform.openai.com/account/api-keys

        self.start_new_chat()

    def ask(self, question: str) -> Iterator[str]:
        self.messages.append({"role": "user", "content": question})
        return stream(self.messages)

    def save_chat(self, file: str):
        save_json(file, {"messages": self.messages})

    def load_chat(self, file: str):
        if os.path.isfile(file):
            data = load_json(file)
            self.messages = data["messages"]

    def start_new_chat(self):
        self.messages.clear()
        self.messages.append(
            {"role": "system", "content": "You are a helpful assistant."}
        )
        clear_terminal()


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
    chat = ChatAPI()
    for chunk in chat.ask(input):
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


def start_conversation(
    *,
    input: Optional[str] = None,
    prompt_text: Optional[str] = None,
    chat_history: Optional[str] = None,
):
    def ask_question(question):
        print("> ", end="")
        for chunk in chat.ask(question):
            print(chunk, end="")
        print()

        if chat_history:
            chat.save_chat(chat_history)

    chat = ChatAPI()

    # Load existing chat
    if chat_history:
        chat.load_chat(chat_history)

    for message in chat.messages:
        if message["role"] != "system":
            print(f"> {message['content']}")

    if input and os.path.isfile(input):
        with open(input, "r", encoding="utf-8") as f:
            input = f.read()

    if input and prompt_text:
        input = prompt_text + "\n\n\n" + input
        ask_question(input)

    try:
        while True:
            question = builtins.input("> ")
            if question == "":
                chat.start_new_chat()

            else:
                ask_question(question)

    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    main()
