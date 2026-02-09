import argparse

from _ext import edit_script


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--line", "-l", type=int)
    args = parser.parse_args()
    edit_script(args.path, line=args.line)


if __name__ == "__main__":
    _main()
