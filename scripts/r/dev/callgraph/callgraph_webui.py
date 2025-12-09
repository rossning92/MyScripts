import argparse
import os
import webbrowser
from threading import Timer
from urllib.parse import urlencode

from dev.callgraph.callgraph import generate_call_graph
from dev.callgraph.mermaid_callgraph import render_mermaid_flowchart
from flask import Flask, request
from utils.logger import setup_logger

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__)


@app.route("/")
def index():
    if files_param := request.args.get("files"):
        files = [f.strip() for f in files_param.split(",")]
    else:
        files = []

    regex = request.args.get("regex")

    match_callers_str = request.args.get("match_callers")
    match_callers: int | None = int(match_callers_str) if match_callers_str else None

    match_callees_str = request.args.get("match_callees")
    match_callees: int | None = int(match_callees_str) if match_callees_str else None

    direction = "LR"
    annotate = None

    call_graph = generate_call_graph(
        files=files,
        regex=regex,
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
    arg_parser.add_argument("--root", default=os.environ.get("PROJECT_ROOT"))

    args = arg_parser.parse_args()

    root = args.root
    if root:
        os.chdir(root)

    setup_logger()

    Timer(
        1.0,
        lambda: webbrowser.open(
            f"http://localhost:{args.port}/?{urlencode({"cwd":os.getcwd()})}"
        ),
    ).start()
    app.run(host="0.0.0.0", port=args.port, debug=True)


if __name__ == "__main__":
    _main()
