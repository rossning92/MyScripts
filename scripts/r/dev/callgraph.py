import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from queue import Queue
from typing import DefaultDict, List, Optional, Set, Tuple

from dev.sourcelang import filename_to_lang
from tree_sitter import Node, Query, Tree
from tree_sitter_language_pack import get_language, get_parser
from utils.defaultordereddict import DefaultOrderedDict
from utils.orderedset import OrderedSet

SCOPE_SEP = "::"
CLASS_PREFIX = ""


def _get_node_text(node):
    return node.text.decode()


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


def _parse_tree(
    lang: str,
    module: str,
    tree: Tree,
) -> Tuple[List[str], DefaultOrderedDict]:
    query = _get_query(lang=lang)
    matches = query.matches(tree.root_node)
    stack: List[Tuple[str, Node]] = []

    functions: List[str] = []
    calls: DefaultOrderedDict = DefaultOrderedDict(OrderedSet)

    for _, match in matches:
        if "definition.function" in match:
            node = match["definition.function"][0]
            name = _get_node_text(match["name.definition.function"][0])
        elif "definition.class" in match:
            node = match["definition.class"][0]
            name = _get_node_text(match["name.definition.class"][0])
        elif "reference.call" in match:
            node = match["reference.call"][0]
            name = _get_node_text(match["name.reference.call"][0]) + "()"
        else:
            continue

        while len(stack) > 0 and not (
            node.start_point >= stack[-1][1].start_point
            and node.end_point <= stack[-1][1].end_point
        ):
            stack.pop()

        if "scope" in match:
            scope = _get_node_text(match["scope"][0])
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


def _get_query(lang: str) -> Query:
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


def _get_module_name(filepath: str, use_full_path=False):
    lang = filename_to_lang(filepath)
    if not use_full_path:
        filepath = os.path.basename(filepath)
    if lang == "cpp":
        return os.path.splitext(filepath)[0] + ".o"
    else:
        return filepath


def _add_module_node(graph: CallGraph, module: str) -> None:
    graph.nodes.add(module)


@lru_cache(maxsize=None)
def _get_tree(file: str) -> Tree:
    parser = get_parser(filename_to_lang(file))

    # Read source code
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()
    return parser.parse(source_code.encode())


def _add_callers_or_callees_to_graph(
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


def _filter_graph(
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
                    _add_callers_or_callees_to_graph(
                        node=node,
                        max_depth=match_callers,
                        graph=graph,
                        new_graph=filtered_graph,
                        find_callers=True,
                    )

                if match_callees is not None:
                    _add_callers_or_callees_to_graph(
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


def generate_call_graph(
    files: List[str],
    match: Optional[str] = None,
    match_callers: Optional[int] = None,
    match_callees: Optional[int] = None,
    ignore_case=False,
) -> CallGraph:
    graph = CallGraph()

    calls = DefaultOrderedDict(OrderedSet)

    # Add nodes
    logging.info("Build nodes...")
    for file in files:
        logging.info(f"Process file: {file}")

        lang = filename_to_lang(file)
        module = _get_module_name(file)
        tree = _get_tree(file)

        _add_module_node(
            graph=graph,
            module=module,
        )

        functions, calls2 = _parse_tree(
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
                    logging.info(f"Call: {caller} -> {callee}")

    return _filter_graph(
        graph=graph,
        match=match,
        match_callers=match_callers,
        match_callees=match_callees,
        ignore_case=ignore_case,
    )
