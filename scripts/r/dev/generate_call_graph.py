import argparse
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, List, Optional, Set

from _shutil import write_temp_file
from tree_sitter import Language, Node, Parser, Query
from utils.editor import open_in_vscode


def filename_to_lang(filename: str) -> str:
    # fmt: off
    ext_language_dict = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".go": "go", ".bash": "bash", ".c": "c", ".cc": "cpp", ".cs": "c_sharp", ".cl": "commonlisp", ".cpp": "cpp", ".css": "css", ".dockerfile": "dockerfile", ".dot": "dot", ".el": "elisp", ".ex": "elixir", ".elm": "elm", ".et": "embedded_template", ".erl": "erlang", ".gomod": "gomod", ".hack": "hack", ".hs": "haskell", ".hcl": "hcl", ".html": "html", ".java": "java", ".jsdoc": "jsdoc", ".json": "json", ".jl": "julia", ".kt": "kotlin", ".lua": "lua", ".mk": "make", ".m": "objc", ".ml": "ocaml", ".pl": "perl", ".php": "php", ".ql": "ql", ".r": "r", ".R": "r", ".regex": "regex", ".rst": "rst", ".rb": "ruby", ".rs": "rust", ".scala": "scala", ".sql": "sql", ".sqlite": "sqlite", ".toml": "toml", ".tsq": "tsq", ".tsx": "typescript", ".ts": "typescript", ".yaml": "yaml"}
    # fmt: on
    _, ext = os.path.splitext(filename)
    return ext_language_dict[ext]


def get_language(lang: str) -> Language:
    if lang == "cpp":
        import tree_sitter_cpp

        return Language(tree_sitter_cpp.language())
    elif lang == "python":
        import tree_sitter_python

        return Language(tree_sitter_python.language())
    else:
        raise Exception(f"Language {lang} is not supported.")


def get_node_text(node):
    return node.text.decode()


def find_calls(node: Node, call_query) -> List[Node]:
    calls = call_query.captures(node)
    return calls["function_name"] if "function_name" in calls else []


@dataclass
class CallGraph:
    nodes: Set[str] = field(default_factory=set)
    edges: DefaultDict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))


def build_nodes(graph: CallGraph, node: Node, function_query: Query):
    matches = function_query.matches(node)
    for _, match in matches:
        name = match["name"][0]
        if "scope" in match:
            scope = match["scope"][0]
            caller_text = get_node_text(scope) + "::" + get_node_text(name)
        else:
            caller_text = get_node_text(name)

        graph.nodes.add(caller_text)


def build_edges(graph: CallGraph, node: Node, call_query: Query, function_query: Query):
    matches = function_query.matches(node)
    for _, match in matches:
        name = match["name"][0]
        if "scope" in match:
            scope = match["scope"][0]
            caller_text = get_node_text(scope) + "::" + get_node_text(name)
        else:
            caller_text = get_node_text(name)

        function = match["function"][0]

        # Add edge to call graph
        for function_name_node in find_calls(function, call_query=call_query):
            callee_text = get_node_text(function_name_node)

            matched_function_names = [
                function_name
                for function_name in graph.nodes
                if re.search(r"\b" + callee_text + "$", function_name)
            ]
            for callee in matched_function_names:
                graph.nodes.add(callee)
                graph.edges[caller_text].add(callee)


def generate_call_graph(files: List[str]) -> CallGraph:
    graph = CallGraph()
    for first_pass in [True, False]:
        for file in files:
            lang = filename_to_lang(file)

            language = get_language(lang)
            parser = Parser(language)

            # Create queries
            if lang == "python":
                call_query = language.query("(call function: (identifier) @call)")
            else:
                call_query = language.query(
                    """\
(call_expression function: (identifier) @function_name)

(call_expression
  function:
    (field_expression
      argument:
        (identifier)
      field:
        (field_identifier)
      @function_name))
"""
                )

            function_query = language.query(
                """\
(function_definition
declarator: (function_declarator
    declarator: (qualified_identifier
    scope: (namespace_identifier) @scope
    name: (identifier) @name))) @function

(function_definition
  declarator: (function_declarator
    declarator: (identifier) @name)) @function
"""
            )

            # Read source code
            with open(file, "r") as f:
                source_code = f.read()
            tree = parser.parse(source_code.encode())

            if first_pass:
                build_nodes(graph, node=tree.root_node, function_query=function_query)
            else:
                build_edges(
                    graph,
                    node=tree.root_node,
                    call_query=call_query,
                    function_query=function_query,
                )

    return graph


def generate_mermaid_flowchart(
    graph: CallGraph, include: Optional[str] = None, class_method_only=False
) -> str:
    class_functions: DefaultDict[str, Set[str]] = defaultdict(set)
    global_functions: Set[str] = set()
    for function_name in graph.nodes:
        if "::" in function_name:
            class_name, function_name = function_name.split("::")
            class_functions[class_name].add(function_name)
        elif not class_method_only:
            global_functions.add(function_name)

    s = "flowchart LR\n"

    if not class_method_only:
        for function_name in global_functions:
            s += f"    {function_name}\n"
        s += "\n"

    for class_name, function_names in class_functions.items():
        s += f"    subgraph {class_name}\n"
        for function_name in function_names:
            s += f'        {class_name}::{function_name}["{function_name}"]\n'
        s += "    end\n"
    s += "\n"

    for caller, callees in graph.edges.items():
        for callee in callees:
            if class_method_only and ("::" not in caller or "::" not in callee):
                continue

            if include:
                if re.search(include, caller, re.IGNORECASE) or re.search(
                    include, callee, re.IGNORECASE
                ):
                    s += f"    {caller} --> {callee}\n"
            else:
                s += f"    {caller} --> {callee}\n"

    return s


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--include", nargs="?", type=str)
    arg_parser.add_argument("-o", "--output", type=str, default=None)
    arg_parser.add_argument("files", nargs="+")

    args = arg_parser.parse_args()

    call_graph = generate_call_graph(args.files)

    # Generate Mermaid flow chart
    s = generate_mermaid_flowchart(call_graph, include=args.include)
    if args.output:
        out_file = args.output
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(s)
    else:
        out_file = write_temp_file(text=s, file_path=".mmd")
    open_in_vscode(out_file)


if __name__ == "__main__":
    _main()
