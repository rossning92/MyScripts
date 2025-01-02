import argparse
import itertools
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from glob import glob
from io import StringIO
from typing import DefaultDict, Dict, List, Optional, Set

from _shutil import write_temp_file
from tree_sitter import Language, Node, Parser, Query, Tree
from utils.editor import open_in_vscode
from utils.logger import setup_logger

SCOPE_SEP = "::"


ext_language_dict = {
    ".py": "python",
    ".h": "cpp",
    ".c": "cpp",
    ".cc": "cpp",
    ".cpp": "cpp",
}


def is_supported_file(file: str) -> bool:
    _, ext = os.path.splitext(file)
    return ext.lower() in ext_language_dict


def filename_to_lang(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext_language_dict[ext.lower()]


@lru_cache(maxsize=None)
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


def _find_first_identifier(node: Node) -> Optional[str]:
    if node.type == "identifier":
        return get_node_text(node)

    for n in node.children:
        id = _find_first_identifier(n)
        if id:
            return id

    return None


def _find_function_calls(node: Node) -> List[str]:
    if node.type == "call_expression":
        function_node = node.child_by_field_name("function_body")
        assert function_node is not None
        id = _find_first_identifier(function_node)
        assert id is not None
        return [id]

    out: List[str] = []
    for n in node.children:
        out += _find_function_calls(n)
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


def add_function_nodes(
    graph: CallGraph,
    module: str,
    root_node: Node,
):
    query = get_cpp_function_definition_query()
    matches = query.matches(root_node)
    for _, match in matches:
        name = match["name"][0]
        if "scope" in match:
            scope = match["scope"][0]
            caller_text = (
                module
                + SCOPE_SEP
                + get_node_text(scope)
                + SCOPE_SEP
                + get_node_text(name)
            )
            graph.scope.scopes[module].scopes[get_node_text(scope)].nodes.add(
                caller_text
            )
        else:
            caller_text = module + SCOPE_SEP + get_node_text(name)
            graph.scope.scopes[module].nodes.add(caller_text)

        graph.nodes.add(caller_text)


def add_call_edges(graph: CallGraph, module: str, root_node: Node):
    query = get_cpp_function_definition_query()
    matches = query.matches(root_node)
    for _, match in matches:
        name = match["name"][0]
        caller_text = module + SCOPE_SEP
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
                # TODO: remove?
                graph.nodes.add(callee)

                if callee != caller_text:  # avoid self-loop
                    graph.edges[caller_text].add(callee)


@lru_cache(maxsize=None)
def get_cpp_include_query() -> Query:
    language = get_language("cpp")

    return language.query(
        """\
(preproc_include path:
  (string_literal
    (string_content) @path))
"""
    )


@lru_cache(maxsize=None)
def get_cpp_function_definition_query() -> Query:
    language = get_language("cpp")

    return language.query(
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


def get_module_name(filepath: str):
    return os.path.splitext(os.path.basename(filepath))[0] + ".o"


def add_module_edges(graph: CallGraph, root_node: Node, module: str):
    include_query = get_cpp_include_query()

    captures = include_query.captures(root_node)
    if "path" in captures:
        for path_node in captures["path"]:
            path = get_node_text(path_node)
            target_module = get_module_name(path)
            if target_module in graph.nodes and target_module != module:
                graph.edges[module].add(target_module)


def add_module_node(graph: CallGraph, module: str) -> None:
    graph.nodes.add(module)


@lru_cache(maxsize=None)
def get_parser(file: str) -> Parser:
    lang = filename_to_lang(file)
    language = get_language(lang)
    return Parser(language)


@lru_cache(maxsize=None)
def get_tree(file: str) -> Tree:
    parser = get_parser(file)

    # Read source code
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()
    return parser.parse(source_code.encode())


def generate_call_graph(files: List[str], show_modules_only=False) -> CallGraph:
    graph = CallGraph()

    # Build nodes
    logging.info("Build nodes...")
    for file in files:
        logging.info(f"Process file: {file}")

        tree = get_tree(file)

        module = get_module_name(file)

        add_module_node(
            graph=graph,
            module=module,
        )

        if not show_modules_only:
            add_function_nodes(
                graph=graph,
                module=module,
                root_node=tree.root_node,
            )

    # Build edges
    logging.info("Build edges...")
    for file in files:
        logging.info(f"Process file: {file}")

        tree = get_tree(file)

        module = get_module_name(file)

        add_module_edges(
            graph=graph,
            root_node=tree.root_node,
            module=module,
        )

        if not show_modules_only:
            add_call_edges(
                graph=graph,
                module=module,
                root_node=tree.root_node,
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
    arg_parser.add_argument(
        "-M",
        "--show-modules-only",
        action="store_true",
        help="show module level diagram",
    )
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
    call_graph = generate_call_graph(
        files=files, show_modules_only=args.show_modules_only
    )

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
