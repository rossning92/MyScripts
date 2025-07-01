import argparse
import http.server
import os
import socketserver
import webbrowser
from urllib.parse import quote


def open_trace_in_browser(path: str, url: str):
    # HTTP Server used to open the trace in the browser.
    class HttpHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            return super().end_headers()

        def do_GET(self):
            self.server.last_request = self.path
            return super().do_GET()

        def do_POST(self):
            self.send_error(404, "File not found")

    # Reuse the HTTP+RPC port because it's the only one allowed by the CSP.
    PORT = 9001

    path = os.path.abspath(path)
    os.chdir(os.path.dirname(path))
    fname = quote(os.path.basename(path))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), HttpHandler) as httpd:
        webbrowser.open_new_tab(f"{url}/#!/?url=http://127.0.0.1:{PORT}/{fname}")
        while httpd.__dict__.get("last_request") != "/" + fname:
            httpd.handle_request()
            print("last_request:", httpd.__dict__.get("last_request"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument(
        "--url",
        type=str,
        default="https://ui.perfetto.dev",
        help="The base URL to use for Perfetto UI",
    )
    args = parser.parse_args()

    open_trace_in_browser(args.file, args.url)
