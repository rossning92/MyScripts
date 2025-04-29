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
    is_supported_file,
)
from utils.diffutils import extract_modified_files_and_line_ranges
from utils.editor import open_in_vscode
from utils.logger import setup_logger
from utils.menu.dicteditmenu import DictEditMenu
from utils.menu.filemenu import FileMenu
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
            raise Exception(f'Failed to create a simplified name: "{name}"')
        else:
            return self.name_map[name]


def escape_mermaid_node(name: str):
    return re.sub(r"\b(call)\b", r"\1_", name)


def render_mermaid_nodes(
    graph: CallGraph,
    scope: Scope,
    short_name: ShortName,
    direction: str,
    annotate: Optional[List[Tuple[str, str]]],
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
                    + short_name.get(escape_mermaid_node(name))
                    + f'["{short_name.get(escape_mermaid_node(name))}<br/><br/>({annotation})"]\n'
                )
            else:
                out.write(indent + short_name.get(escape_mermaid_node(name)) + "\n")

            # Highlight node
            if name in graph.highlighted_nodes:
                out.write(
                    f"{indent}style {short_name.get(escape_mermaid_node(name))} color:red\n"
                )

    return out.getvalue()


def render_mermaid_flowchart(
    graph: CallGraph,
    direction: str,
    annotate: Optional[List[Tuple[str, str]]],
) -> str:
    s = f"flowchart {direction}\n"

    short_name = ShortName()

    s += render_mermaid_nodes(
        graph=graph,
        scope=graph.scope,
        short_name=short_name,
        direction=direction,
        annotate=annotate,
    )

    for caller, callees in graph.edges.items():
        for callee in callees:
            s += f"    {short_name.get(escape_mermaid_node(caller))} --> {short_name.get(escape_mermaid_node(callee))}\n"

    return s


class CallGraphMenu(DictEditMenu):
    def on_enter_pressed(self):
        key = self.get_selected_key()
        if key is None:
            return

        if key == "files":
            file_menu = FileMenu()
            file = file_menu.select_file()
            if file:
                self.set_dict_value("files", file)
        else:
            return super().on_enter_pressed()


def run_interactive_menu():
    menu = CallGraphMenu(
        data={
            "files": "",
            "match": "",
            "match_callers": 0,
            "match_callees": 0,
        }
    )
    menu.exec()


def _main():
    # run_interactive_menu()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-E", "--match", nargs="?", type=str)
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
    arg_parser.add_argument("--annotate", type=str)
    arg_parser.add_argument("--include-all-identifiers", action="store_true")
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
        include_all_identifiers=args.include_all_identifiers,
    )

    # Generate mermaid diagram
    mermaid_code = render_mermaid_flowchart(
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
