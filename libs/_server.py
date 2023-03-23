import json
import logging
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST_NAME = "127.0.0.1"
PORT = 4312


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
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

    def log_message(self, format, *args):
        return


def server_thread():
    server = HTTPServer((HOST_NAME, PORT), MyServer)
    logging.info("Script server started http://%s:%s" % (HOST_NAME, PORT))
    server.serve_forever()
    server.server_close()
    print("Script server stopped.")


def start_server(start_new_thread=False):
    if start_new_thread:
        threading.Thread(target=server_thread, daemon=True).start()
    else:
        server_thread()


if __name__ == "__main__":
    try:
        server_thread()
    except KeyboardInterrupt:
        pass
