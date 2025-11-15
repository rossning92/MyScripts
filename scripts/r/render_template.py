import argparse
import os

from utils.template import render_template_file


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()

    render_template_file(args.input_file, args.output_file, context=os.environ)


if __name__ == "__main__":
    _main()
