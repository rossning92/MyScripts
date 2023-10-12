import json
import logging
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import unquote

from _script import get_data_dir, get_my_script_root
from _shutil import load_json, save_json

HOST_NAME = "127.0.0.1"


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def _serve_file(self, path):
        with open(path, "rb") as f:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f.read())

    def do_GET(self):
        try:
            if self.path.startswith("/fs/"):
                file_path = self.path.removeprefix("/fs/")
                file_path = unquote(file_path)
                self._serve_file(file_path)

            elif self.path == "/userscriptlib.js":
                self._serve_file(
                    os.path.join(
                        get_my_script_root(),
                        "js",
                        "userscriptlib",
                        "dist",
                        "userscriptlib.js",
                    )
                )

        except IOError:
            self.send_error(404, "File Not Found: %s" % self.path)

    def do_POST(self):
        try:
            if self.path == "/system":
                data = self.read_json()
                out = subprocess.check_output(
                    args=data["args"], universal_newlines=True, encoding="utf-8"
                )

                logging.info("/%s: response: %s" % (self.path, out))
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=UTF-8")
                self.end_headers()
                self.wfile.write(out.encode("utf-8"))

            elif self.path == "/load-data":
                req = self.read_json()
                data_file = os.path.join(get_data_dir(), f"{req['name']}.json")
                data = load_json(data_file, {})
                self.send_json({"success": True, "data": data})

            elif self.path == "/save-data":
                req = self.read_json()
                data_file = os.path.join(get_data_dir(), f"{req['name']}.json")
                save_json(data_file, req["data"])
                self.send_json({"success": True})

            else:
                return self.send_response(500)
        except Exception:
            logging.exception("")

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def read_json(self):
        data_string = self.rfile.read(int(self.headers["Content-Length"]))
        data = json.loads(data_string.decode("utf-8"))
        logging.info("%s: request: %s" % (self.path, data))
        return data

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        return


class ScriptServer:
    def __init__(self, port=4312) -> None:
        self.port = port
        self.t: Optional[threading.Thread] = None

    def _server_main(self):
        server = ThreadingHTTPServer((HOST_NAME, self.port), MyHTTPRequestHandler)
        logging.info(
            "Script API server started at: http://%s:%s" % (HOST_NAME, self.port)
        )
        server.serve_forever()
        server.server_close()
        print("Script server stopped.")

    def start_server(self):
        self.t = threading.Thread(target=self._server_main, daemon=True)
        self.t.start()

    def join_server_thread(self):
        if self.t is None:
            raise Exception("Server is not started.")
        self.t.join()
