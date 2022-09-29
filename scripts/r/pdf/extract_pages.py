import os

from _shutil import call_echo, get_files

if __name__ == "__main__":
    in_file = get_files()[0]
    out_file = os.path.splitext(in_file)[0] + ".p{{_RANGE}}.pdf"
    call_echo(["pdftk", in_file, "cat"] + "{{_RANGE}}".split() + ["output", out_file])
