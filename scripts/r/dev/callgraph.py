import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from queue import Queue
from typing import DefaultDict, Dict, Iterator, List, Optional, Set, Tuple

from dev.sourcelang import filename_to_lang
from tree_sitter import Node, Query, Tree
from tree_sitter_language_pack import get_language, get_parser
from utils.defaultordereddict import DefaultOrderedDict
from utils.orderedset import OrderedSet

SCOPE_SEP = "::"
CLASS_PREFIX = ""


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
    if node.type == "function_definition":
        return []

    if node.type == "identifier" or node.type == "field_identifier":
        return [get_node_text(node)]

    out: List[str] = []
    for n in node.children:
        out += _find_all_identifiers(n)
    return out


@dataclass
class Scope:
    # It's important to maintain the order of each child to know which function is called first and which one is called afterward.
    scopes: DefaultOrderedDict = field(
        default_factory=lambda: DefaultOrderedDict(Scope)
    )


@dataclass
class CallGraph:
    nodes: Set[str] = field(default_factory=set)

    edges: DefaultDict[str, OrderedSet[str]] = field(
        default_factory=lambda: defaultdict(OrderedSet)
    )
    reverse_edges: DefaultDict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    scope: Scope = field(default_factory=Scope)

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


def parse_tree(
    lang: str,
    module: str,
    tree: Tree,
) -> Tuple[List[str], DefaultOrderedDict]:
    query = get_query(lang=lang)
    matches = query.matches(tree.root_node)
    stack: List[Tuple[str, Node]] = []

    functions: List[str] = []
    calls: DefaultOrderedDict = DefaultOrderedDict(OrderedSet)

    for _, match in matches:
        if "definition.function" in match:
            node = match["definition.function"][0]
            name = get_node_text(match["name.definition.function"][0])
        elif "definition.class" in match:
            node = match["definition.class"][0]
            name = get_node_text(match["name.definition.class"][0])
        elif "reference.call" in match:
            node = match["reference.call"][0]
            name = get_node_text(match["name.reference.call"][0]) + "()"
        else:
            continue

        while len(stack) > 0 and not (
            node.start_point >= stack[-1][1].start_point
            and node.end_point <= stack[-1][1].end_point
        ):
            stack.pop()

        if "scope" in match:
            scope = get_node_text(match["scope"][0])
            name = scope + SCOPE_SEP + name

            # WORKAROUND: For C++ qualified function definitions, sometimes
            # TreeSitter incorrectly parses one function to be inside another
            # function. The following code works around this bug.
            while len(stack) > 0 and stack[-1][0].startswith(scope + SCOPE_SEP):
                stack.pop()

        if "reference.call" in match:
            caller = SCOPE_SEP.join([module] + [x[0] for x in stack])
            callee = name
            if caller != module:
                calls[caller].add(callee)
        else:
            stack.append((name, node))

        if "definition.function" in match:
            full_name = SCOPE_SEP.join([module] + [x[0] for x in stack])
            functions.append(full_name)

    return functions, calls


def get_query(lang: str) -> Query:
    query_scm_file = os.path.join(
        Path(__file__).parent.resolve(),
        "tree_sitter",
        "queries",
        f"{lang}.scm",
    )
    language = get_language(lang)
    with open(query_scm_file, "r") as f:
        source = f.read()
    return Query(language, source)


def get_function_definitions(
    lang: str,
    module: str,
    root_node: Node,
) -> Iterator[Tuple[str, Node]]:
    query = get_function_definition_query(lang=lang)
    matches = query.matches(root_node)
    for _, match in matches:
        function_def = match["function_def"][0]
        name = match["function_name"][0]
        if "class_name" in match:
            class_name = match["class_name"][0]
            yield (
                module
                + SCOPE_SEP
                + CLASS_PREFIX
                + get_node_text(class_name)
                + SCOPE_SEP
                + get_node_text(name),
                function_def,
            )

        else:
            yield (
                module + SCOPE_SEP + get_node_text(name),
                function_def,
            )


def create_edges(
    lang: str,
    graph: CallGraph,
    module: str,
    root_node: Node,
    include_all_identifiers: bool,
):
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

        # Add edge to call graph
        for identifier in _find_all_identifiers(function_body_node):
            # Add edge callee
            is_callee = False
            found_function_names = [
                function_name
                for function_name in graph.nodes
                if re.search(r"\b" + identifier + "$", function_name)
            ]
            for callee in found_function_names:
                if callee != caller_text:  # avoid self-loop
                    graph.add_edge(caller_text, callee)
                    logging.info(f"Add function call: {caller_text} -> {callee}")
                    is_callee = True

            # Add edge to other identifiers
            if not is_callee and include_all_identifiers:
                graph.add_edge(caller_text, identifier)


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


def get_module_name(filepath: str, use_full_path=False):
    lang = filename_to_lang(filepath)
    if not use_full_path:
        filepath = os.path.basename(filepath)
    if lang == "cpp":
        return os.path.splitext(filepath)[0] + ".o"
    else:
        return filepath


def add_module_edges(graph: CallGraph, root_node: Node, module: str):
    query = get_cpp_include_query()
    captures = query.captures(root_node)
    if "path" in captures:
        for path_node in captures["path"]:
            path = get_node_text(path_node)
            target_module = get_module_name(path)
            if target_module in graph.nodes and target_module != module:
                graph.add_edge(module, target_module)


def add_module_node(graph: CallGraph, module: str) -> None:
    graph.nodes.add(module)


@lru_cache(maxsize=None)
def get_tree(file: str) -> Tree:
    parser = get_parser(filename_to_lang(file))

    # Read source code
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()
    return parser.parse(source_code.encode())


def add_callers_or_callees_to_graph(
    node: str,
    max_depth: int,
    graph: CallGraph,
    new_graph: CallGraph,
    find_callers: bool,
):
    q: Queue[Tuple[str, int]] = Queue()
    q.put((node, 0))
    while not q.empty():
        n, d = q.get()
        if d < max_depth:
            for connected_node in (
                graph.reverse_edges[n] if find_callers else graph.edges[n]
            ):
                new_graph.add_node(connected_node)
                q.put((connected_node, d + 1))


def generate_call_graph(
    files: List[str],
    show_modules_only=False,
    match: Optional[str] = None,
    invert_match: Optional[str] = None,
    match_callers: Optional[int] = None,
    match_callees: Optional[int] = None,
    diff: Optional[Dict[str, List[Tuple[int, int]]]] = None,
    ignore_case=False,
    include_all_identifiers=False,
) -> CallGraph:
    graph = CallGraph()

    # Add nodes
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
            for function_name, function_def_node in get_function_definitions(
                lang=lang,
                module=module,
                root_node=tree.root_node,
            ):
                logging.info(
                    f"Add function node: {function_name} ({function_def_node.start_point.row}-{function_def_node.end_point.row})"
                )
                graph.add_node(function_name)

                # # Filter nodes
                # if diff:
                #     for line_range in diff[file]:
                #         if max(
                #             function_def_node.start_point.row, line_range[0] - 1
                #         ) <= min(function_def_node.end_point.row, line_range[1] - 1):
                #             filtered_nodes.add(function_name)

    # Add edges
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
                include_all_identifiers=include_all_identifiers,
            )

    return filter_graph(
        graph=graph,
        match=match,
        match_callers=match_callers,
        match_callees=match_callees,
        ignore_case=ignore_case,
    )


def filter_graph(
    graph: CallGraph,
    match: Optional[str] = None,
    match_callers: Optional[int] = None,
    match_callees: Optional[int] = None,
    ignore_case=False,
) -> CallGraph:
    filtered_nodes: Set[str] = set()

    # Filter nodes
    for n in graph.nodes:
        if match and re.search(match, n, re.IGNORECASE if ignore_case else 0):
            filtered_nodes.add(n)

    if filtered_nodes:
        filtered_graph = CallGraph()

        for node in graph.nodes:
            if node in filtered_nodes:
                # Add filtered nodes
                filtered_graph.add_node(node)
                filtered_graph.highlighted_nodes.add(node)

                # Add caller and callee nodes
                if match_callers is not None:
                    add_callers_or_callees_to_graph(
                        node=node,
                        max_depth=match_callers,
                        graph=graph,
                        new_graph=filtered_graph,
                        find_callers=True,
                    )

                if match_callees is not None:
                    add_callers_or_callees_to_graph(
                        node=node,
                        max_depth=match_callees,
                        graph=graph,
                        new_graph=filtered_graph,
                        find_callers=False,
                    )

        # Add edges
        for caller, callees in graph.edges.items():
            for callee in callees:
                if caller in filtered_graph.nodes and callee in filtered_graph.nodes:
                    filtered_graph.add_edge(caller, callee)

        return filtered_graph
    else:
        return graph


def generate_call_graph_new(
    files: List[str],
    show_modules_only=False,
    match: Optional[str] = None,
    invert_match: Optional[str] = None,
    match_callers: Optional[int] = None,
    match_callees: Optional[int] = None,
    diff: Optional[Dict[str, List[Tuple[int, int]]]] = None,
    ignore_case=False,
    include_all_identifiers=False,
) -> CallGraph:
    graph = CallGraph()

    calls = DefaultOrderedDict(OrderedSet)

    # Add nodes
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

        functions, calls2 = parse_tree(
            lang=lang,
            module=module,
            tree=tree,
        )

        for function_name in functions:
            graph.add_node(function_name)
        calls.update(calls2)

    # Add edges
    for caller, callees in calls.items():
        for callee in callees:
            matched_callees = [
                function_name
                for function_name in graph.nodes
                if re.search(r"\b" + callee + "$", function_name)
            ]
            for callee in matched_callees:
                if callee != caller:  # avoid self-loop
                    graph.add_edge(caller, callee)
                    logging.info(f"Add function call: {caller} -> {callee}")

    return filter_graph(
        graph=graph,
        match=match,
        match_callers=match_callers,
        match_callees=match_callees,
        ignore_case=ignore_case,
    )
