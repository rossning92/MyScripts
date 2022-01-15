import os
import re
import subprocess
import tempfile

from _shutil import cd, get_files, get_hash, shell_open

HEADER = os.path.realpath("_header.tex")

f = get_files()[0]

cd(os.path.dirname(f))
infile = os.path.basename(f)


outfile = os.path.splitext(infile)[0]
if "{{_GEN_TEX}}":
    outfile += ".tex"
elif "{{_GEN_DOCX}}":
    outfile += ".docx"
else:
    outfile += ".pdf"


print(f"{infile} => {outfile}")

s = open(f, encoding="utf-8").read()


def generate_diagram(match):
    if match.group(1).strip() == "dot2":
        s = """digraph G {
        rankdir=LR

        graph [fontsize=14 dpi=300]
        node [shape=record fontname="Source Han Serif CN"]
        // node [fontname="Latin Modern Mono"]
        // edge [fontname="Latin Modern Mono"]

        // labelloc="t"
        // label=<<font point-size="18"><b>TITLE</b></font><br/><br/><br/>>

        // splines=polyline
        // splines=ortho

        %s
    }""" % match.group(
            2
        )

        tmpfile = os.path.join(tempfile.gettempdir(), get_hash(s) + ".png")

        print("Generating %s" % tmpfile)
        p = subprocess.Popen(["dot", "-Tpng", "-o", tmpfile], stdin=subprocess.PIPE)
        p.stdin.write(s.encode("utf-8"))
        p.stdin.close()
        ret = p.wait()
        if ret != 0:
            raise Exception("dot returns non zero.")

        return "![](%s)" % tmpfile.replace("\\", "/")

    return "[unsupported diagram]"


def eval_python_code(match):
    python_code = match.group(1)
    result = eval(python_code, globals())
    if result is not None:
        return str(result)
    else:
        return ""


if __name__ == "__main__":
    s = re.sub(r"```(\w+)\n([\d\D]*?)```", generate_diagram, s)
    s = re.sub(r"\{\{([\d\D]*?)\}\}", eval_python_code, s)

    print("Generating pdf...")
    p = subprocess.Popen(
        [
            "pandoc",
            "--pdf-engine=xelatex",
            "-o",
            outfile,
            "--wrap=preserve",
            "-f",
            "gfm+hard_line_breaks",
            "-H",
            HEADER,
            "-V",
            "documentclass=extarticle",
            "-V",
            "fontsize=14pt",
            "-V",
            "CJKmainfont=Source Han Serif CN",
            "-V",
            "geometry=margin=1in",
            "--dpi=300",
            "-V",
            "papersize:a4",
        ],
        stdin=subprocess.PIPE,
    )

    if p.stdin is not None:
        p.stdin.write(s.encode("utf-8"))
        p.stdin.close()
    ret = p.wait()
    if ret != 0:
        raise Exception("pandoc returns non zero")

    shell_open(outfile)
