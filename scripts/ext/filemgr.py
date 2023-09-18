import argparse

from _filemgr import FileManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "goto",
        nargs="?",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    FileManager(goto=args.goto).exec()
