import os

from _shutil import call_echo, get_files
from utils.shutil import shell_open

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    infile = os.path.basename(f)
    outfile = os.path.splitext(infile)[0] + ".pdf"
    print(f"{infile} => {outfile}")

    args = [
        "pandoc",
        "--pdf-engine=xelatex",
        "-o",
        outfile,
        "--wrap=preserve",
        "-f",
        "gfm+hard_line_breaks",
        "-V",
        "documentclass=extarticle",
        "-V",
        "CJKmainfont=Source Han Serif CN",
        "-V",
        "geometry=margin=1in",
        "--dpi=300",
        "-V",
        "papersize:a4",
    ]

    if "{{FONT_SIZE}}":
        args += ["-V", "fontsize:{{FONT_SIZE}}pt"]

    args.append(infile)

    call_echo(args)

    shell_open(outfile)
