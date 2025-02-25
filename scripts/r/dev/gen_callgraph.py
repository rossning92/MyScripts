import argparse
import itertools
import os
import re
import subprocess
import sys
from glob import glob
from io import StringIO
from typing import Dict, Set

from callgraph import (
    SCOPE_SEP,
    CallGraph,
    Scope,
    generate_call_graph,
    is_supported_file,
)
from utils.diffutils import extract_modified_files_and_line_ranges
from utils.editor import open_in_vscode
from utils.logger import setup_logger
from utils.shutil import shell_open
from utils.template import render_template_file
from utils.temputil import get_temp_file

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class ShortName:
    def __init__(self) -> None:
        self.name_map: Dict[str, str] = {}  # original name -> short name
        self.used_name: Set[str] = set()  # already used short names

    def get(self, name: str) -> str:
        if name not in self.name_map:
            arr = name.split(SCOPE_SEP)
            for i in reversed(range(len(arr))):
                new_name = SCOPE_SEP.join(arr[i:])
                if new_name not in self.used_name:
                    self.used_name.add(new_name)
                    self.name_map[name] = new_name
                    return new_name
            raise Exception("Failed to create a simplified name")
        else:
            return self.name_map[name]


def escape_mermaid_node(name: str):
    return re.sub(r"\b(call)\b", r"\1_", name)


def render_mermaid_nodes(
    graph: CallGraph,
    scope: Scope,
    short_name: ShortName,
    direction: str,
    depth=1,
) -> str:
    out = StringIO()
    indent = " " * 4 * depth
    for name, s in scope.scopes.items():
        if len(s.scopes) > 0:
            out.write(
                indent + "subgraph " + short_name.get(escape_mermaid_node(name)) + "\n"
            )
            out.write(indent + f"    direction {direction}\n\n")
            out.write(
                render_mermaid_nodes(
                    graph=graph,
                    scope=s,
                    short_name=short_name,
                    direction=direction,
                    depth=depth + 1,
                )
            )
            out.write(indent + "end\n\n")
        else:
            out.write(indent + short_name.get(escape_mermaid_node(name)) + "\n")
            if name in graph.highlighted_nodes:
                out.write(
                    f"{indent}style {short_name.get(escape_mermaid_node(name))} color:red\n"
                )

    return out.getvalue()


def render_mermaid_flowchart(graph: CallGraph, direction: str) -> str:
    s = f"flowchart {direction}\n"

    short_name = ShortName()

    s += render_mermaid_nodes(
        graph=graph, scope=graph.scope, short_name=short_name, direction=direction
    )

    for caller, callees in graph.edges.items():
        for callee in callees:
            s += f"    {short_name.get(escape_mermaid_node(caller))} --> {short_name.get(escape_mermaid_node(callee))}\n"

    return s


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--match", nargs="?", type=str)
    arg_parser.add_argument("-v", "--invert-match", nargs="?", type=str)
    arg_parser.add_argument("-o", "--output", type=str, default=None)
    arg_parser.add_argument("--match-callers", nargs="?", type=int, const=1)
    arg_parser.add_argument("--match-callees", nargs="?", type=int, const=1)
    arg_parser.add_argument("--direction", type=str, default="LR")

    arg_parser.add_argument(
        "-M",
        "--show-modules-only",
        action="store_true",
        help="show module level diagram",
    )
    arg_parser.add_argument("--diff", type=str)
    arg_parser.add_argument("files", nargs="*")

    args = arg_parser.parse_args()

    setup_logger()

    if args.diff:
        diff = extract_modified_files_and_line_ranges(args.diff)
        files = list(diff.keys())
    else:
        diff = None
        files = [
            filepath.replace(os.path.sep, "/")
            for filepath in itertools.chain(
                *[glob(pathname, recursive=True) for pathname in args.files]
            )
        ]
        files = [f for f in files if is_supported_file(f)]
    files = [f for f in files if is_supported_file(f)]

    # Generate call graph
    call_graph = generate_call_graph(
        files=files,
        show_modules_only=args.show_modules_only,
        match=args.match,
        invert_match=args.invert_match,
        match_callers=args.match_callers,
        match_callees=args.match_callees,
        diff=diff,
    )

    # Generate mermaid diagram
    mermaid_code = render_mermaid_flowchart(graph=call_graph, direction=args.direction)
    if args.output:
        out_file = args.output
    else:
        out_file = get_temp_file(".html")

    ext = os.path.splitext(out_file)[1].lower()
    if ext == ".svg":
        process = subprocess.Popen(
            [
                "npx",
                "-p",
                "@mermaid-js/mermaid-cli",
                "mmdc",
                "-o",
                out_file,
                "--input",
                "-",
            ],
            stdin=subprocess.PIPE,
            shell=sys.platform == "win32",
        )
        process.communicate(input=mermaid_code.encode())
        process.wait()
        shell_open(out_file)

    elif ext == ".html":
        render_template_file(
            template_file=os.path.join(SCRIPT_DIR, "mermaid_viewer.html"),
            output_file=out_file,
            context={"MERMAID_CODE": mermaid_code},
        )
        shell_open(out_file)

    else:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        open_in_vscode(out_file)


if __name__ == "__main__":
    _main()
