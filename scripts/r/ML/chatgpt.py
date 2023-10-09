import argparse
import os
import sys
from typing import Dict, Iterator, List, Optional

import openai
from _shutil import load_json, pause, save_json, set_clip
from utils.menu import Menu


class Chat:
    def __init__(self, stream_mode: bool = True) -> None:
        self.stream_mode = stream_mode
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

        # https://platform.openai.com/account/api-keys
        openai.api_key = os.environ["OPENAI_API_KEY"]

    def ask(self, question: str) -> Iterator[str]:
        self.messages.append({"role": "user", "content": question})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            stream=self.stream_mode,
        )

        try:
            if self.stream_mode:
                full_response = ""
                for chunk in response:
                    chunk_message = chunk["choices"][0]["delta"]  # type: ignore
                    if "content" in chunk_message:
                        content = chunk_message["content"]
                        full_response += content
                        yield content

            else:
                full_response = response["choices"][0]["message"]["content"]  # type: ignore
                yield full_response

            self.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                }
            )

        except (BrokenPipeError, IOError):
            pass

    def save_chat(self, file: str):
        save_json(file, {"messages": self.messages})

    def load_chat(self, file: str):
        if os.path.isfile(file):
            data = load_json(file)
            self.messages = data["messages"]


def complete_chat(
    *,
    input_text: str,
    prompt_text: Optional[str] = None,
    copy_to_clipboard: bool = False,
    pause_after_completion: bool = False,
):
    if prompt_text:
        input_text = prompt_text + "\n\n" + input_text

    full_response = ""
    chat = Chat()
    for chunk in chat.ask(input_text):
        full_response += chunk
        print(chunk, end="")

    if copy_to_clipboard:
        set_clip(full_response)

    if pause_after_completion:
        print("\n\n")
        pause()

    return full_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?", default=None)
    parser.add_argument("-c", "--copy-to-clipboard", action="store_true", default=False)
    parser.add_argument("-p", "--load-prompt-file", action="store_true", default=False)
    args = parser.parse_args()

    if args.input and os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            input_text = f.read()

        complete_chat(
            input_text=input_text,
            copy_to_clipboard=args.copy_to_clipboard,
        )

    elif args.input:
        input_text = args.input

        # Load custom prompts
        if args.load_prompt_file:
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
            input_text=input_text,
            prompt_text=prompt_text,
            copy_to_clipboard=args.copy_to_clipboard,
        )

    else:  # empty
        conversation()


def conversation():
    config_file = os.path.join(os.environ["MY_DATA_DIR"], "chatgpt_conversation.json")
    chat = Chat()
    chat.load_chat(config_file)
    for message in chat.messages:
        if message["role"] != "system":
            print(f"> {message['content']}")

    try:
        while True:
            question = input("> ")
            print("> ", end="")
            for chunk in chat.ask(question):
                print(chunk, end="")
            print("")
            chat.save_chat(config_file)

    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    main()
