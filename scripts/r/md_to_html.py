from _shutil import *


def convert_md_to_html(file):
    out_file = os.path.splitext(file)[0] + ".html"
    call_echo(["pandoc", "-s", "-c", "pandoc.css", file, "-o", out_file])
    return out_file


if __name__ == "__main__":

    in_file = get_files(cd=True)[0]
    out_file = convert_md_to_html(in_file)
    shell_open(out_file)
