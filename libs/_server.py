import logging
import subprocess
import threading

import flask
from flask import Flask, Response, request

app = Flask(__name__)


def start_server(disable_logging=False, start_new_thread=False):
    if disable_logging:
        log = logging.getLogger("werkzeug")
        log.disabled = True
        app.logger.disabled = True
        flask.cli.show_server_banner = lambda *_: None

    run = lambda: app.run("127.0.0.1", 4312)
    if start_new_thread:
        threading.Thread(target=run).start()
    else:
        run()


@app.route("/")
def index():
    return (
        '<form action="/exec" method="post">'
        '  <input type="text" name="args" value="echo hello">'
        '  <input type="submit" value="Submit">'
        "</form>"
    )


@app.route("/exec", methods=["POST"])
def exec():
    args = request.form["args"]
    out = subprocess.check_output(args=args, shell=True, universal_newlines=True)
    response = Response(out)
    response.headers["content-type"] = "text/plain"
    return response


if __name__ == "__main__":
    start_server()
