import argparse

from ai.chat_menu import ChatMenu, get_default_data_dir


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", nargs="?", type=str)
    parser.add_argument(
        "-x",
        "--copy",
        action="store_true",
        help="Copy the last message and then exit",
    )

    args = parser.parse_args()

    chat = ChatMenu(
        context=args.context,
        copy=args.copy,
        data_dir=get_default_data_dir(),
    )
    chat.exec()


if __name__ == "__main__":
    _main()
