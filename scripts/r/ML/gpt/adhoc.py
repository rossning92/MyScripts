import argparse
import os

from r.ML.gpt.chatgpt import start_conversation
from utils.menu.textinput import TextInput

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str)
    args = parser.parse_args()

    prompt_text = TextInput(
        history_file=os.path.join(
            os.environ["MY_DATA_DIR"], "adhoc_prompt_history.json"
        )
    ).request_input()
    if prompt_text:
        start_conversation(
            input=args.input,
            prompt_text=prompt_text,
        )
