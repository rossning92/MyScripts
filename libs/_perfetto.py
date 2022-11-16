import http.server
import os
import socketserver
import subprocess
import time
import webbrowser

from _shutil import call_echo, setup_logger

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace


setup_logger()


def open_trace_in_browser(path):
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

    # We reuse the HTTP+RPC port because it's the only one allowed by the CSP.
    PORT = 9001
    os.chdir(os.path.dirname(path))
    fname = os.path.basename(path)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), HttpHandler) as httpd:
        webbrowser.open_new_tab(
            "https://ui.perfetto.dev/#!/?url=http://127.0.0.1:%d/%s" % (PORT, fname)
        )
        while httpd.__dict__.get("last_request") != "/" + fname:
            httpd.handle_request()


def start_trace(config_str, open_trace=True, detached_mode=False):
    ps = subprocess.Popen(
        [
            r"protoc",
            "--encode=perfetto.protos.TraceConfig",
            "-I",
            ".",
            "protos/perfetto/config/perfetto_config.proto",
        ],
        stdin=subprocess.PIPE,
        stdout=open("config.bin", "wb"),
    )
    ps.stdin.write(config_str.encode())
    ps.stdin.close()
    ps.wait()

    call_echo(["adb", "shell", "killall perfetto"], check=False)
    call_echo(
        ["adb", "push", "config.bin", "/data/misc/perfetto-traces/config.bin"],
        check=True,
    )

    if detached_mode:
        pid = subprocess.check_output(
            [
                "adb",
                "shell",
                "perfetto",
                "-c",
                "/data/misc/perfetto-traces/config.bin",
                "-o",
                "/data/misc/perfetto-traces/trace",
                "--background",
            ],
        )
        pid = int(pid)

        input("press enter to stop perfetto (PID=%d)..." % pid)
        call_echo(["adb", "shell", "kill -9 %d" % pid])
        time.sleep(5)

    else:
        call_echo(
            [
                "adb",
                "shell",
                "perfetto",
                "-c",
                "/data/misc/perfetto-traces/config.bin",
                "-o",
                "/data/misc/perfetto-traces/trace",
            ],
            check=True,
        )

    call_echo(["adb", "pull", "/data/misc/perfetto-traces/trace", "/tmp/trace"])

    if open_trace:
        open_trace_in_browser("/tmp/trace")
