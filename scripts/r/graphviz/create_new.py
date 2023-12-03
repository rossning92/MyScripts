from _editor import *
from _shutil import *

cd(r"{{GRAPHVIZ_SRC_FOLDER}}")

template = """
digraph G {
    rankdir=LR;
    node [shape=record]

    graph [fontname="Roboto" dpi=200];
    node [fontname="Roboto"];
    edge [fontname="Roboto"];
    node [shape=record]

    // labelloc="t"
    // label=<<font point-size="18"><b>TITLE</b></font><br/><br/><br/>>

    //splines=polyline
    // splines=ortho

    a -> b -> c -> d
}
""".strip()

fn = "%s.dot" % get_cur_time_str()
with open(fn, "w") as f:
    f.write(template)

open_code_editor(fn)
