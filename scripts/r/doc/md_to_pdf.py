import argparse
import os
import subprocess
import sys

from utils.shutil import shell_open


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input Markdown file")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    style_path = os.path.join(script_dir, "letter.css")

    # --border-top=1mm --border-bottom=1mm

    cmd = ["mdpdf", "--format=Letter"]

    if os.getenv("USE_LETTER_STYLE") == "1":
        cmd.insert(1, "--style=" + style_path)

    cmd.append(args.file)

    subprocess.check_call(cmd, shell=sys.platform == "win32")

    if os.getenv("NO_OPEN") != "1":
        output_pdf = args.file.replace(".md", ".pdf")
        shell_open(output_pdf)


if __name__ == "__main__":
    _main()
