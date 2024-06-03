import os

from _shutil import call_echo, get_files
from utils.shutil import shell_open


def convert_md_to_html(file):
    out_file = os.path.splitext(file)[0] + ".html"
    style = os.path.abspath(os.path.dirname(__file__) + "/pandoc.css")
    call_echo(
        [
            "pandoc",
            "-f",
            "markdown",
            "-t",
            "html5",
            "-o",
            out_file,
            "-c",
            style,
            "--standalone",
            "--self-contained",
            file,
        ]
    )
    return out_file


if __name__ == "__main__":
    in_file = get_files(cd=True)[0]
    out_file = convert_md_to_html(in_file)
    shell_open(out_file)
