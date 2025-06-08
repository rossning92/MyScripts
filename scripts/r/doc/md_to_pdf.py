import argparse
import os
import subprocess
import sys

from utils.shutil import shell_open


def markdown_to_pdf(input_file: str, use_letter_style=False, open_pdf_file=False):
    cmd = ["mdpdf", "--format=Letter"]

    if use_letter_style:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        style_path = os.path.join(script_dir, "letter.css")
        cmd.insert(1, "--style=" + style_path)

    cmd.append(input_file)

    subprocess.check_call(cmd, shell=sys.platform == "win32")

    if open_pdf_file:
        output_pdf = input_file.replace(".md", ".pdf")
        shell_open(output_pdf)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input Markdown file")
    args = parser.parse_args()

    markdown_to_pdf(
        input_file=args.file,
        use_letter_style=os.getenv("USE_LETTER_STYLE") == "1",
        open_pdf_file=os.getenv("NO_OPEN") != "1",
    )


if __name__ == "__main__":
    _main()
