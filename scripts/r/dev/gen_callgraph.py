import argparse
import itertools
import os
import re
import subprocess
import sys
from glob import glob
from io import StringIO
from typing import Dict, List, Optional, Set, Tuple

from callgraph import (
    SCOPE_SEP,
    CallGraph,
    Scope,
    generate_call_graph,
)
from dev.sourcelang import is_supported_file
from utils.editor import open_in_vscode
from utils.logger import setup_logger
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.filemenu import FileMenu
from utils.shutil import shell_open
from utils.template import render_template_file
from utils.temputil import get_temp_file

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class _ShortName:
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
            raise Exception(f'Failed to create a simplified name: "{name}"')
        else:
            return self.name_map[name]


def _escape_mermaid_node(name: str):
    return re.sub(r"\b(call|end)\b", r"_\1_", name)


def _render_mermaid_nodes(
    graph: CallGraph,
    scope: Scope,
    short_name: _ShortName,
    direction: str,
    annotate: Optional[List[Tuple[str, str]]],
    depth=1,
) -> str:
    out = StringIO()
    indent = " " * 4 * depth
    for name, s in scope.scopes.items():
        if len(s.scopes) > 0:
            out.write(
                indent + "subgraph " + short_name.get(_escape_mermaid_node(name)) + "\n"
            )
            out.write(indent + f"    direction {direction}\n\n")
            out.write(
                _render_mermaid_nodes(
                    graph=graph,
                    scope=s,
                    short_name=short_name,
                    direction=direction,
                    annotate=annotate,
                    depth=depth + 1,
                )
            )
            out.write(indent + "end\n\n")
        else:
            # Check if there is an annotation for the node.
            annotation = None
            if annotate:
                for k, v in annotate:
                    if k in name:
                        annotation = v

            # Render node
            if annotation:
                out.write(
                    indent
                    + short_name.get(_escape_mermaid_node(name))
                    + f'["{short_name.get(_escape_mermaid_node(name))}<br/><br/>({annotation})"]\n'
                )
            else:
                out.write(indent + short_name.get(_escape_mermaid_node(name)) + "\n")

            # Highlight node
            if name in graph.highlighted_nodes:
                out.write(
                    f"{indent}style {short_name.get(_escape_mermaid_node(name))} color:red\n"
                )

    return out.getvalue()


def _render_mermaid_flowchart(
    graph: CallGraph,
    direction: str,
    annotate: Optional[List[Tuple[str, str]]],
) -> str:
    s = f"flowchart {direction}\n"

    short_name = _ShortName()

    s += _render_mermaid_nodes(
        graph=graph,
        scope=graph.scope,
        short_name=short_name,
        direction=direction,
        annotate=annotate,
    )

    for caller, callees in graph.edges.items():
        for callee in callees:
            s += f"    {short_name.get(_escape_mermaid_node(caller))} --> {short_name.get(_escape_mermaid_node(callee))}\n"

    return s


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--root", type=str, default=None, help="Root dir for source code"
    )
    arg_parser.add_argument("-E", "--match", nargs="?", type=str)
    arg_parser.add_argument("-o", "--output", type=str, default=None)
    arg_parser.add_argument("--match-callers", nargs="?", type=int, const=1)
    arg_parser.add_argument("--match-callees", nargs="?", type=int, const=1)
    arg_parser.add_argument("--direction", type=str, default="LR")
    arg_parser.add_argument("--annotate", type=str)
    arg_parser.add_argument("files", nargs="*")

    args = arg_parser.parse_args()

    setup_logger()

    if args.root:
        os.chdir(args.root)

    if args.files:
        files = [
            filepath.replace(os.path.sep, "/")
            for filepath in itertools.chain(
                *[glob(pathname, recursive=True) for pathname in args.files]
            )
        ]
        files = [f for f in files if is_supported_file(f)]
    else:
        files = subprocess.check_output(
            ["rg", "-l", args.match], universal_newlines=True
        ).splitlines()

    files = [file.replace(os.path.sep, "/") for file in files]
    files = [file for file in files if is_supported_file(file)]

    # Generate call graph
    call_graph = generate_call_graph(
        files=files,
        match=args.match,
        match_callers=args.match_callers,
        match_callees=args.match_callees,
    )

    # Generate mermaid diagram
    mermaid_code = _render_mermaid_flowchart(
        graph=call_graph,
        direction=args.direction,
        annotate=(
            [kvp.split("=") for kvp in args.annotate.split(";")]
            if args.annotate
            else None
        ),
    )
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
            template_file=os.path.join(_SCRIPT_DIR, "mermaid_viewer.html"),
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
