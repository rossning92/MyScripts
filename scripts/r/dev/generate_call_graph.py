import argparse
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from typing import DefaultDict, Dict, List, Optional, Set

from _shutil import write_temp_file
from tree_sitter import Language, Node, Parser, Query
from utils.editor import open_in_vscode

SCOPE_SEP = "::"


def filename_to_lang(filename: str) -> str:
    # fmt: off
    ext_language_dict = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".go": "go", ".bash": "bash", ".c": "cpp", ".cc": "cpp", ".cs": "c_sharp", ".cl": "commonlisp", ".cpp": "cpp", ".css": "css", ".dockerfile": "dockerfile", ".dot": "dot", ".el": "elisp", ".ex": "elixir", ".elm": "elm", ".et": "embedded_template", ".erl": "erlang", ".gomod": "gomod", ".hack": "hack", ".hs": "haskell", ".hcl": "hcl", ".html": "html", ".java": "java", ".jsdoc": "jsdoc", ".json": "json", ".jl": "julia", ".kt": "kotlin", ".lua": "lua", ".mk": "make", ".m": "objc", ".ml": "ocaml", ".pl": "perl", ".php": "php", ".ql": "ql", ".r": "r", ".R": "r", ".regex": "regex", ".rst": "rst", ".rb": "ruby", ".rs": "rust", ".scala": "scala", ".sql": "sql", ".sqlite": "sqlite", ".toml": "toml", ".tsq": "tsq", ".tsx": "typescript", ".ts": "typescript", ".yaml": "yaml"}
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


def _find_first_identifier(node: Node) -> Optional[str]:
    if node.type == "identifier":
        return get_node_text(node)

    for n in node.children:
        id = _find_first_identifier(n)
        if id:
            return id

    return None


def find_function_calls(node: Node) -> List[str]:
    if node.type == "call_expression":
        function_node = node.child_by_field_name("function_body")
        assert function_node is not None
        id = _find_first_identifier(function_node)
        assert id is not None
        return [id]

    out: List[str] = []
    for n in node.children:
        out += find_function_calls(n)
    return out


def _find_all_identifiers(node: Node) -> List[str]:
    if node.type == "identifier" or node.type == "field_identifier":
        return [get_node_text(node)]

    out: List[str] = []
    for n in node.children:
        out += _find_all_identifiers(n)
    return out


@dataclass
class Scope:
    nodes: Set[str] = field(default_factory=set)
    scopes: DefaultDict = field(default_factory=lambda: defaultdict(Scope))


@dataclass
class CallGraph:
    nodes: Set[str] = field(default_factory=set)
    edges: DefaultDict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    scope: Scope = field(default_factory=Scope)


def build_nodes(graph: CallGraph, filename: str, node: Node, function_query: Query):
    matches = function_query.matches(node)
    for _, match in matches:
        name = match["name"][0]
        if "scope" in match:
            scope = match["scope"][0]
            caller_text = (
                filename
                + SCOPE_SEP
                + get_node_text(scope)
                + SCOPE_SEP
                + get_node_text(name)
            )
            graph.scope.scopes[filename].scopes[get_node_text(scope)].nodes.add(
                caller_text
            )
        else:
            caller_text = filename + SCOPE_SEP + get_node_text(name)
            graph.scope.scopes[filename].nodes.add(caller_text)

        graph.nodes.add(caller_text)


def build_edges(graph: CallGraph, filename: str, node: Node, function_query: Query):
    matches = function_query.matches(node)
    for _, match in matches:
        name = match["name"][0]
        caller_text = filename + SCOPE_SEP
        if "scope" in match:
            scope = match["scope"][0]
            caller_text += get_node_text(scope) + SCOPE_SEP
        caller_text += get_node_text(name)

        function_node = match["function_body"][0]

        # Add edge to call graph
        for callee_text in _find_all_identifiers(function_node):
            matched_function_names = [
                function_name
                for function_name in graph.nodes
                if re.search(r"\b" + callee_text + "$", function_name)
            ]
            for callee in matched_function_names:
                graph.nodes.add(callee)

                if callee != caller_text:  # avoid self-loop
                    graph.edges[caller_text].add(callee)


def generate_call_graph(files: List[str]) -> CallGraph:
    graph = CallGraph()
    for first_pass in [True, False]:
        for file in files:
            lang = filename_to_lang(file)

            language = get_language(lang)
            parser = Parser(language)

            function_query = language.query(
                """\
(function_definition
  declarator: (function_declarator
    declarator: (qualified_identifier
      scope: (namespace_identifier) @scope
      name: (identifier) @name))
  body: (compound_statement) @function_body)

(function_definition
  declarator: (function_declarator
    declarator: (identifier) @name)
  body: (compound_statement) @function_body)
"""
            )

            # Read source code
            with open(file, "r") as f:
                source_code = f.read()
            tree = parser.parse(source_code.encode())

            filename = os.path.basename(file)

            if first_pass:
                build_nodes(
                    graph,
                    filename=filename,
                    node=tree.root_node,
                    function_query=function_query,
                )
            else:
                build_edges(
                    graph,
                    filename=filename,
                    node=tree.root_node,
                    function_query=function_query,
                )

    return graph


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


def render_mermaid_scope(
    scope: Scope, short_name: ShortName, visible_nodes: Optional[Set[str]], depth=1
) -> str:
    out = StringIO()
    for node in scope.nodes:
        if visible_nodes is None or node in visible_nodes:
            out.write((" " * depth * 4) + short_name.get(node) + "\n")
    for name, s in scope.scopes.items():
        out.write((" " * depth * 4) + "subgraph " + short_name.get(name) + "\n")
        out.write(
            render_mermaid_scope(
                scope=s,
                short_name=short_name,
                visible_nodes=visible_nodes,
                depth=depth + 1,
            )
        )
        out.write((" " * depth * 4) + "end\n\n")
    return out.getvalue()


def render_mermaid_flowchart(graph: CallGraph, include: Optional[str] = None) -> str:
    s = "flowchart\n"

    short_name = ShortName()

    visible_nodes: Optional[Set[str]] = None
    if include:
        visible_nodes = set()
        for caller, callees in graph.edges.items():
            for callee in callees:
                if re.search(include, caller, re.IGNORECASE) or re.search(
                    include, callee, re.IGNORECASE
                ):
                    visible_nodes.add(caller)
                    visible_nodes.add(callee)

    s += render_mermaid_scope(
        scope=graph.scope, short_name=short_name, visible_nodes=visible_nodes
    )

    for caller, callees in graph.edges.items():
        for callee in callees:
            if include:
                if re.search(include, caller, re.IGNORECASE) or re.search(
                    include, callee, re.IGNORECASE
                ):
                    s += f"    {short_name.get(caller)} --> {short_name.get(callee)}\n"
            else:
                s += f"    {short_name.get(caller)} --> {short_name.get(callee)}\n"

    return s


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--include", nargs="?", type=str)
    arg_parser.add_argument("-o", "--output", type=str, default=None)
    arg_parser.add_argument("files", nargs="+")

    args = arg_parser.parse_args()

    call_graph = generate_call_graph(args.files)

    # Generate mermaid diagram
    s = render_mermaid_flowchart(call_graph, include=args.include)
    if args.output:
        out_file = args.output
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(s)
    else:
        out_file = write_temp_file(text=s, file_path=".mmd")
    open_in_vscode(out_file)


if __name__ == "__main__":
    _main()
