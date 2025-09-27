import argparse

from ML.gpt.chat_menu import ChatMenu


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attachment", nargs="?", type=str)
    parser.add_argument(
        "-x",
        "--copy",
        action="store_true",
        help="Copy the last message and then exit",
    )

    args = parser.parse_args()

    chat = ChatMenu(
        attachment=args.attachment,
        copy=args.copy,
    )
    chat.exec()


if __name__ == "__main__":
    _main()
