import argparse
import itertools
import os
import subprocess
import sys
from glob import glob

from dev.callgraph.callgraph import generate_call_graph
from dev.callgraph.mermaid_callgraph import render_mermaid_flowchart
from dev.callgraph.sourcelang import is_supported_file
from utils.editor import open_in_vscode
from utils.logger import setup_logger
from utils.shutil import shell_open
from utils.template import render_template_file
from utils.temputil import get_temp_file

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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
