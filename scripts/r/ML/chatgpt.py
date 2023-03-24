import argparse
import os

import openai

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default="What's 1+1? Answer in one english word.",
    )
    args = parser.parse_args()

    # https://platform.openai.com/account/api-keys
    openai.api_key = os.environ["OPEN_AI_API_KEY"]
    model_engine = "gpt-3.5-turbo"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": args.input},
        ],
        stream=True,
    )

    for chunk in response:
        chunk_message = chunk["choices"][0]["delta"]
        if "content" in chunk_message:
            print(chunk_message["content"], end="")
