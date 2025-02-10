import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from queue import Queue
from typing import DefaultDict, Dict, Iterator, List, Optional, Set, Tuple

from tree_sitter import Language, Node, Parser, Query, Tree

SCOPE_SEP = "::"
CLASS_PREFIX = ""


ext_language_dict = {
    ".c": "cpp",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".h": "cpp",
    ".frag": "cpp",
    ".vert": "cpp",
    ".glsl": "cpp",
    ".hpp": "cpp",
    ".py": "python",
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


def _find_all_identifiers(node: Node) -> List[str]:
    if node.type == "identifier" or node.type == "field_identifier":
        return [get_node_text(node)]

    out: List[str] = []
    for n in node.children:
        out += _find_all_identifiers(n)
    return out


@dataclass
class Scope:
    scopes: DefaultDict = field(default_factory=lambda: defaultdict(Scope))


@dataclass
class CallGraph:
    nodes: Set[str] = field(default_factory=set)

    edges: DefaultDict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_edges: DefaultDict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    scope: Scope = field(default_factory=Scope)

    node_preview: Dict[str, str] = field(default_factory=dict)

    highlighted_nodes: Set[str] = field(default_factory=set)

    def add_scope(self, name: str):
        full_name = []
        scope = self.scope
        for identifier in name.split(SCOPE_SEP):
            full_name.append(identifier)
            scope = scope.scopes[SCOPE_SEP.join(full_name)]

    def add_node(self, node: str):
        self.nodes.add(node)
        self.add_scope(name=node)

    def add_edge(self, from_node: str, to_node: str):
        # Avoid self-loop
        if from_node == to_node:
            return

        self.add_node(from_node)
        self.add_node(to_node)

        self.edges[from_node].add(to_node)
        self.reverse_edges[to_node].add(from_node)


def get_function_definitions(
    lang: str,
    module: str,
    root_node: Node,
    generate_preview: bool,
) -> Iterator[Tuple[str, Optional[str], Node]]:
    query = get_function_definition_query(lang=lang)
    matches = query.matches(root_node)
    for _, match in matches:
        function_def = match["function_def"][0]
        if generate_preview:
            function_preview = get_node_text(function_def).splitlines()[0]
        else:
            function_preview = None
        name = match["function_name"][0]
        if "class_name" in match:
            class_name = match["class_name"][0]
            yield (
                (
                    module
                    + SCOPE_SEP
                    + CLASS_PREFIX
                    + get_node_text(class_name)
                    + SCOPE_SEP
                    + get_node_text(name)
                ),
                function_preview,
                function_def,
            )

        else:
            yield (
                module + SCOPE_SEP + get_node_text(name),
                function_preview,
                function_def,
            )


def create_edges(lang: str, graph: CallGraph, module: str, root_node: Node):
    query = get_function_definition_query(lang=lang)
    matches = query.matches(root_node)
    for _, match in matches:
        name = match["function_name"][0]
        caller_text = module + SCOPE_SEP
        if "class_name" in match:
            class_name = match["class_name"][0]
            caller_text += CLASS_PREFIX + get_node_text(class_name) + SCOPE_SEP
        caller_text += get_node_text(name)

        function_body_node = match["function_body"][0]

        logging.info(f"Find callees from: {caller_text}")

        # Add edge to call graph
        for identifier in _find_all_identifiers(function_body_node):
            matched_function_names = [
                function_name
                for function_name in graph.nodes
                if re.search(r"\b" + identifier + "$", function_name)
            ]
            for callee in matched_function_names:
                if callee != caller_text:  # avoid self-loop
                    graph.add_edge(caller_text, callee)


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
def get_function_definition_query_cpp() -> Query:
    language = get_language("cpp")

    return language.query(
        """\
(function_definition
  declarator: (function_declarator
    declarator: (identifier) @function_name)
  body: (compound_statement) @function_body) @function_def

(function_definition
  declarator: (pointer_declarator
    declarator: (function_declarator
      declarator: (identifier) @function_name))
  body: (compound_statement) @function_body) @function_def

(class_specifier
  name: (type_identifier) @class_name
  body: (field_declaration_list
    (function_definition
      declarator: (function_declarator
        declarator: (field_identifier) @function_name)
      body: (compound_statement) @function_body) @function_def))

(function_definition
  declarator: (function_declarator
    declarator: (qualified_identifier
      scope: (namespace_identifier) @class_name
      name: (identifier) @function_name))
  body: (compound_statement) @function_body) @function_def
"""
    )


@lru_cache(maxsize=None)
def get_function_definition_query_python() -> Query:
    language = get_language("python")

    return language.query(
        """\
(module
  (function_definition
    name: (identifier) @function_name
    body: (block) @function_body) @function_def)

(module
  (class_definition
    name: (identifier) @class_name
    body: (block
      (function_definition
        name: (identifier) @function_name
        body: (block) @function_body) @function_def)))
"""
    )


@lru_cache(maxsize=None)
def get_function_definition_query(lang: str) -> Query:
    if lang == "cpp":
        return get_function_definition_query_cpp()
    elif lang == "python":
        return get_function_definition_query_python()
    else:
        raise Exception(f"Language '{lang}' is not supported")


def get_module_name(filepath: str):
    lang = filename_to_lang(filepath)
    if lang == "cpp":
        return os.path.splitext(os.path.basename(filepath))[0] + ".o"
    else:
        return filepath


def add_module_edges(graph: CallGraph, root_node: Node, module: str):
    include_query = get_cpp_include_query()

    captures = include_query.captures(root_node)
    if "path" in captures:
        for path_node in captures["path"]:
            path = get_node_text(path_node)
            target_module = get_module_name(path)
            if target_module in graph.nodes and target_module != module:
                graph.add_edge(module, target_module)


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


def add_callers_or_callees_to_graph(
    node: str,
    max_depth: int,
    graph: CallGraph,
    new_graph: CallGraph,
    should_find_callers: bool,
):
    q: Queue[Tuple[str, int]] = Queue()
    q.put((node, 0))
    while not q.empty():
        n, d = q.get()
        if d < max_depth:
            for connected_node in (
                graph.reverse_edges[n] if should_find_callers else graph.edges[n]
            ):
                if should_find_callers:
                    new_graph.add_edge(connected_node, n)
                else:
                    new_graph.add_edge(n, connected_node)
                q.put((connected_node, d + 1))


def generate_call_graph(
    files: List[str],
    show_modules_only=False,
    match: Optional[str] = None,
    invert_match: Optional[str] = None,
    match_callers: Optional[int] = None,
    match_callees: Optional[int] = None,
    generate_preview=False,
    diff: Optional[Dict[str, List[Tuple[int, int]]]] = None,
) -> CallGraph:
    graph = CallGraph()

    filtered_nodes: Set[str] = set()

    # Build nodes
    logging.info("Build nodes...")
    for file in files:
        logging.info(f"Process file: {file}")

        lang = filename_to_lang(file)
        module = get_module_name(file)
        tree = get_tree(file)

        add_module_node(
            graph=graph,
            module=module,
        )

        if not show_modules_only:
            for function_name, preview, function_def_node in get_function_definitions(
                lang=lang,
                module=module,
                root_node=tree.root_node,
                generate_preview=generate_preview,
            ):
                # Add node
                logging.info(
                    f"Add function node: {function_name} ({function_def_node.start_point.row}-{function_def_node.end_point.row})"
                )
                graph.add_node(function_name)
                if preview:
                    graph.node_preview[function_name] = preview

                # Filter nodes
                if diff:
                    for line_range in diff[file]:
                        if max(
                            function_def_node.start_point.row, line_range[0] - 1
                        ) <= min(function_def_node.end_point.row, line_range[1] - 1):
                            filtered_nodes.add(function_name)

                if match and re.search(match, function_name, re.IGNORECASE):
                    filtered_nodes.add(function_name)

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
            create_edges(
                lang=lang,
                graph=graph,
                module=module,
                root_node=tree.root_node,
            )

    if filtered_nodes:
        filtered_graph = CallGraph()

        for node in graph.nodes:
            if node in filtered_nodes:
                filtered_graph.add_node(node)
                filtered_graph.highlighted_nodes.add(node)

                if match_callers is not None:
                    add_callers_or_callees_to_graph(
                        node=node,
                        max_depth=match_callers,
                        graph=graph,
                        new_graph=filtered_graph,
                        should_find_callers=True,
                    )

                if match_callees is not None:
                    add_callers_or_callees_to_graph(
                        node=node,
                        max_depth=match_callees,
                        graph=graph,
                        new_graph=filtered_graph,
                        should_find_callers=False,
                    )

        for caller, callees in graph.edges.items():
            for callee in callees:
                if caller in filtered_graph.nodes and callee in filtered_graph.nodes:
                    filtered_graph.add_edge(caller, callee)

        graph = filtered_graph

    return graph
