import argparse
import os

import openai
from _script import get_data_dir
from _shutil import load_json, set_clip
from _term import select_option

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default="What's 1+1? Answer in one english word.",
    )
    parser.add_argument("--copy-to-clipboard", action="store_true", default=False)
    parser.add_argument("--custom-prompts", action="store_true", default=False)
    args = parser.parse_args()

    input_ = args.input
    if args.custom_prompts:
        options = load_json(
            os.path.join(get_data_dir(), "custom_prompts.json"),
        )
        idx = select_option(options, history_file_name="custom_prompts")
        prompt_text = options[idx]
        input_ = prompt_text + "\n\n" + input_

    # https://platform.openai.com/account/api-keys
    openai.api_key = os.environ["OPEN_AI_API_KEY"]
    model_engine = "gpt-3.5-turbo"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_},
        ],
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
