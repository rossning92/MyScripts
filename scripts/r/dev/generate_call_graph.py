import os
import subprocess
from collections import defaultdict
from typing import DefaultDict, List, Optional, Set

from _shutil import write_temp_file
from tree_sitter import Language, Node, Parser


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


def find_first_identifier_recursively(node: Node) -> Optional[Node]:
    if node.type == "identifier":
        return node
    for child in node.children:
        identifier = find_first_identifier_recursively(child)
        if identifier:
            return identifier
    return None


def find_calls(node: Node, call_query) -> List[Node]:
    calls = call_query.captures(node)
    return calls["call"] if "call" in calls else []


def find_function_definitions(node: Node, function_query) -> List[Node]:
    functions = function_query.captures(node)
    return functions["function"] if "function" in functions else []


def generate_call_graph(
    root: Node, call_query, function_query
) -> DefaultDict[str, Set[str]]:
    call_graph = defaultdict(set)

    for func in find_function_definitions(root, function_query=function_query):
        caller = find_first_identifier_recursively(func)

        for callee in find_calls(func, call_query=call_query):
            call_graph[get_node_text(caller)].add(get_node_text(callee))

    return call_graph


def generate_mermaid_flowchart(call_graph: DefaultDict[str, Set[str]]) -> str:
    callers = set(call_graph.keys())

    s = "flowchart LR\n"
    for caller in callers:
        s += f"    {caller}\n"
    s += "\n"

    for caller, callees in call_graph.items():
        for callee in callees:
            if callee in callers:
                s += f"    {caller} --> {callee}\n"
    return s


def _main():
    fname = os.environ["_FILE"]
    lang = filename_to_lang(fname)

    language = get_language(lang)
    parser = Parser(language)

    # Create queries
    if lang == "python":
        call_query = language.query("(call function: (identifier) @call)")
    else:
        call_query = language.query("(call_expression function: (identifier) @call)")

    function_query = language.query("(function_definition) @function")

    # Read source code
    with open(
        fname,
        "r",
    ) as file:
        source_code = file.read()
    tree = parser.parse(source_code.encode())

    # Generate call graph
    call_graph = generate_call_graph(
        tree.root_node, call_query=call_query, function_query=function_query
    )
    s = generate_mermaid_flowchart(call_graph)
    file = write_temp_file(text=s, file_path=".mmd")
    subprocess.call([r"C:\Program Files\Microsoft VS Code\bin\code.cmd", file])


if __name__ == "__main__":
    _main()
