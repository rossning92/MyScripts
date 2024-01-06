import argparse
import os

from ML.gpt.chatgpt import ChatMenu
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
        if os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input
        chat = ChatMenu(first_message=prompt_text + ":\n---\n" + input_text)
        chat.exec()
