import argparse
import itertools
import os
from glob import glob
from io import StringIO

from callgraph import (
    generate_call_graph,
    is_supported_file,
)
from dev.callgraph import CallGraph, Scope
from utils.logger import setup_logger

TAB_SIZE = 2


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("files", nargs="+")

    args = arg_parser.parse_args()

    setup_logger()

    files = [
        filepath.replace(os.path.sep, "/")
        for filepath in itertools.chain(
            *[glob(pathname, recursive=True) for pathname in args.files]
        )
    ]
    files = [f for f in files if is_supported_file(f)]
    call_graph = generate_call_graph(files=files, generate_preview=True)

    s = render_repomap(graph=call_graph, scope=call_graph.scope)
    print(s)


def render_repomap(graph: CallGraph, scope: Scope, depth=0) -> str:
    out = StringIO()
    indent = " " * TAB_SIZE * depth
    for name, s in scope.scopes.items():
        if len(s.scopes) > 0:
            out.write(indent + name + ":\n")
            out.write(
                render_repomap(
                    graph=graph,
                    scope=s,
                    depth=depth + 1,
                )
            )
            out.write("\n\n")
        else:

            out.write(
                indent
                + (graph.node_preview[name] if name in graph.node_preview else name)
                + "\n"
            )

    return out.getvalue()


if __name__ == "__main__":
    _main()
