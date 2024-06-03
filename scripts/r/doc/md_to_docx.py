import os

from _shutil import call_echo, get_files
from utils.shutil import shell_open


def convert_md_to_docx(file):
    out_file = os.path.splitext(file)[0] + ".docx"
    call_echo(
        [
            "pandoc",
            "-s",
            "-o",
            out_file,
            file,
        ]
    )
    return out_file


if __name__ == "__main__":
    in_file = get_files(cd=True)[0]
    out_file = convert_md_to_docx(in_file)
    shell_open(out_file)
