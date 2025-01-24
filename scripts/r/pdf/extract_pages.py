import os
import subprocess
import sys


def split_pdf(file_path):
    page_range = os.environ["_RANGE"].split()
    base_name = os.path.splitext(file_path)[0]
    out_file = f"{base_name}.p{page_range}.pdf"
    subprocess.check_call(
        ["pdftk", file_path, "cat"] + page_range + ["output", out_file]
    )


if __name__ == "__main__":
    split_pdf(file_path=sys.argv[1])
