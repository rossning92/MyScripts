import argparse

from _ext import edit_script


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    edit_script(args.path, editor="vim")


if __name__ == "__main__":
    _main()
