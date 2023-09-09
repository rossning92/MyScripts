import argparse
import os
import subprocess

import openai
from _shutil import getch, load_json, set_clip
from _term import select_option

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?", default="")
    parser.add_argument("--copy-to-clipboard", action="store_true", default=False)
    parser.add_argument("--custom-prompts", action="store_true", default=False)
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            input_ = f.read()
    elif args.input:
        input_ = args.input
    else:
        input_ = subprocess.check_output(
            ["xclip", "-out", "-selection", "primary"], universal_newlines=True
        )

    # Load custom prompts
    prompt_file = os.path.join(os.environ["MY_DATA_DIR"], "custom_prompts.json")
    if os.path.exists(prompt_file):
        options = load_json(prompt_file)
        idx = select_option(options, history="custom_prompts")
        prompt_text = options[idx]
        input_ = prompt_text + "\n\n" + input_

    # https://platform.openai.com/account/api-keys
    openai.api_key = os.environ["OPENAI_API_KEY"]
    model_engine = "gpt-3.5-turbo"

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": input_},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    )

    full_text = ""
    for chunk in response:
        chunk_message = chunk["choices"][0]["delta"]
        if "content" in chunk_message:
            full_text += chunk_message["content"]
            print(chunk_message["content"], end="")

    if args.copy_to_clipboard:
        set_clip(full_text)
    else:
        print("\n\n(press any key to copy to clipboard...)")
        getch()
        set_clip(full_text)
