from _shutil import *

HEADER = os.path.realpath("_header.tex")

f = get_files()[0]

cd(os.path.dirname(f))
infile = os.path.basename(f)
outfile = os.path.splitext(infile)[0] + ".pdf"

print(f"{infile} => {outfile}")

s = open(f, encoding="utf-8").read()


def generate_diagram(match):
    if match.group(1).strip() == "dot2":
        s = """digraph G {
        rankdir=TB

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

        tmpfile = os.path.join(gettempdir(), get_hash(s) + ".png")

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
    ],
    stdin=subprocess.PIPE,
)
p.stdin.write(s.encode("utf-8"))
p.stdin.close()
p.wait()

shell_open(outfile)
