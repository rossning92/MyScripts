import argparse
import os
import sys
from typing import Optional

import openai
from _menu import Menu
from _shutil import load_json, pause, set_clip


def complete_chat(
    *,
    input_text: str,
    prompt_text: Optional[str] = None,
    copy_to_clipboard: bool = False,
    pause_after_completion: bool = False,
):
    if prompt_text:
        input_text = prompt_text + "\n\n" + input_text

    # https://platform.openai.com/account/api-keys
    openai.api_key = os.environ["OPENAI_API_KEY"]

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": input_text},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    )

    full_text = ""
    try:
        for chunk in response:
            chunk_message = chunk["choices"][0]["delta"]
            if "content" in chunk_message:
                full_text += chunk_message["content"]
                print(chunk_message["content"], end="")
    except (BrokenPipeError, IOError):
        pass

    if copy_to_clipboard:
        set_clip(full_text)

    if pause_after_completion:
        print("\n\n")
        pause()

    return full_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str)
    parser.add_argument("-c", "--copy-to-clipboard", action="store_true", default=False)
    parser.add_argument("-p", "--load-prompt-file", action="store_true", default=False)
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            input_text = f.read()
    else:
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


if __name__ == "__main__":
    main()
