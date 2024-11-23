import json
import logging
import os
import subprocess
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import unquote

from _scriptmanager import ScriptManager
from scripting.path import get_data_dir, get_my_script_root

HOST_NAME = "127.0.0.1"


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, script_manager: ScriptManager, *args, **kwargs):
        self.__script_manager = script_manager
        super().__init__(*args, **kwargs)

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

            elif self.path == "/scripts":
                self._send_json(
                    {
                        "scripts": [
                            {"name": script.name, "path": script.script_path}
                            for script in self.__script_manager.scripts
                        ]
                    }
                )

            else:
                raise Exception(f"Invalid path: {self.path}")

        except Exception as ex:
            self.send_error(500, str(ex))

    def do_POST(self):
        try:
            if self.path == "/system":
                data = self._get_req_data()
                out = subprocess.check_output(
                    args=data["args"], universal_newlines=True, encoding="utf-8"
                )

                logging.info("%s: response: %s" % (self.path, out))
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=UTF-8")
                self.end_headers()
                self.wfile.write(out.encode("utf-8"))

            elif self.path == "/load-file":
                req = self._get_req_data()
                file_path = os.path.join(get_data_dir(), f"{req['file']}")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._send_json({"success": True, "content": content})

            elif self.path == "/save-file":
                req = self._get_req_data()
                file_path = os.path.join(get_data_dir(), f"{req['file']}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(req["content"])
                self._send_json({"success": True, "filePath": file_path})

            else:
                return self.send_response(500)
        except Exception:
            logging.exception("")

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _get_req_data(self):
        data_string = self.rfile.read(int(self.headers["Content-Length"]))
        data = json.loads(data_string.decode("utf-8"))
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
    def __init__(self, script_manager: ScriptManager, port=4312) -> None:
        self.__port = port
        self.__httpd: Optional[ThreadingHTTPServer] = None
        self.__lock = threading.Lock()
        self.__server_thread: Optional[threading.Thread] = None
        self.__script_manager = script_manager

    def _server_main(self):
        handler = partial(MyHTTPRequestHandler, self.__script_manager)
        httpd = ThreadingHTTPServer((HOST_NAME, self.__port), handler)
        with self.__lock:
            self.__httpd = httpd

        logging.info("API server started at: http://%s:%s" % (HOST_NAME, self.__port))
        httpd.serve_forever()
        httpd.server_close()

        with self.__lock:
            self.__httpd = None

        logging.info("API server stopped.")

    def start_server(self):
        if self.__server_thread is not None:
            raise Exception("API server is already started.")
        logging.debug("Starting API server...")
        self.__server_thread = threading.Thread(target=self._server_main, daemon=True)
        self.__server_thread.start()

    def stop_server(self, join_thread=True):
        with self.__lock:
            httpd = self.__httpd

        if httpd is None or self.__server_thread is None:
            raise Exception("API server is not started.")
        logging.debug("Stopping API server...")
        httpd.shutdown()

        if join_thread:
            self.join_server_thread()

    def join_server_thread(self):
        if self.__server_thread is None:
            raise Exception("API server is not started.")
        self.__server_thread.join()
