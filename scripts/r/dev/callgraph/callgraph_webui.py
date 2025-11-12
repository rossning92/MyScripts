import argparse
import os

from dev.callgraph.callgraph import generate_call_graph
from dev.callgraph.mermaid_callgraph import render_mermaid_flowchart
from flask import Flask, request
from utils.logger import setup_logger

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__)


@app.route("/")
def index():
    if not (files_param := request.args.get("files")):
        return "Error: 'files' query parameter is required", 400
    files = [f.strip() for f in files_param.split(",")]

    match = request.args.get("match")

    match_callers = request.args.get("match_callers")
    if match_callers:
        match_callers = int(match_callers)

    match_callees = request.args.get("match_callees")
    if match_callees:
        match_callees = int(match_callees)

    direction = "LR"
    annotate = None

    call_graph = generate_call_graph(
        files=files,
        match=match,
        match_callers=match_callers,
        match_callees=match_callees,
    )

    mermaid_code = render_mermaid_flowchart(
        graph=call_graph,
        direction=direction,
        annotate=annotate,
    )

    template_file = os.path.join(_SCRIPT_DIR, "mermaid_viewer.html")
    with open(template_file, "r") as f:
        template_content = f.read()

    html = template_content.replace("{{MERMAID_CODE}}", mermaid_code)

    return html


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--port", type=int, default=5000)

    args = arg_parser.parse_args()

    setup_logger()

    app.run(host="0.0.0.0", port=args.port, debug=True)


if __name__ == "__main__":
    _main()
