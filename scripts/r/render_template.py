import argparse
import os

from utils.template import render_template


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        s = f.read()

    result = render_template(s, context=os.environ)
    print(result)


if __name__ == "__main__":
    _main()
