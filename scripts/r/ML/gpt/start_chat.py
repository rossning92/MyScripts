import argparse
import os

from ML.gpt.chatgui import ChatMenu

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str)
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()
    else:
        s = args.input
    chat = ChatMenu(first_message=s)
    chat.exec()
