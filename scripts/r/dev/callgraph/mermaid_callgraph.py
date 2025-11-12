import re
from io import StringIO
from typing import Dict, List, Optional, Set, Tuple

from dev.callgraph.callgraph import SCOPE_SEP, CallGraph, Scope


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


def render_mermaid_flowchart(
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
