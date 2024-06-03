from _shutil import *
from utils.shutil import shell_open


def generate_png(s, out_file):
    s = (
        """digraph G {
        rankdir=TB

        graph [fontsize=14 dpi=300]
        node [shape=record fontname="Source Han Serif CN"]
        // node [fontname="Latin Modern Mono"]
        // edge [fontname="Latin Modern Mono"]
        // subgraph [fontname="Source Han Serif CN"]

        // labelloc="t"
        // label=<<font point-size="18"><b>TITLE</b></font><br/><br/><br/>>

        // splines=polyline
        // splines=ortho

        %s
    }"""
        % s
    )

    print("Generating %s" % out_file)
    p = subprocess.Popen(
        ["dot", "-Nfontname=Source Han Serif CN", "-Tpng", "-o", out_file],
        stdin=subprocess.PIPE,
    )
    p.stdin.write(s.encode("utf-8"))
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    f = get_files(cd=True)[0]
    name, ext = os.path.splitext(f)
    if ext != ".dot":
        raise Exception("file extension is not `.dot`")

    with open(f, encoding="utf-8") as f:
        s = f.read()
    generate_png(s, name + ".png")

    shell_open(name + ".png")
