import json
import logging
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST_NAME = "127.0.0.1"


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_POST(self):
        try:
            if self.path != "/exec":
                return self.send_response(500)

            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            data = json.loads(data_string.decode("utf-8"))
            logging.info("/exec: %s" % data)
            out = subprocess.check_output(
                args=data["args"], universal_newlines=True, encoding="utf-8"
            )
            logging.info("/exec: output: %s" % out)
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=UTF-8")
            self.end_headers()
            self.wfile.write(out.encode("utf-8"))
        except Exception:
            logging.exception("")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        return


def _server_main(directory, port):
    handler = partial(MyHTTPRequestHandler, directory)
    server = ThreadingHTTPServer((HOST_NAME, port), handler)
    logging.info("Script server started http://%s:%s" % (HOST_NAME, port))
    server.serve_forever()
    server.server_close()
    print("Script server stopped.")


def start_server(directory=None, port=4312):
    t = threading.Thread(target=_server_main, args=(directory, port), daemon=True)
    t.start()
