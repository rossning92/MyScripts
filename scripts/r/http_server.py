import http.server
import os
import re
from http.server import ThreadingHTTPServer

from _shutil import get_ip_addresses

PORT = 8000
if os.environ.get('HTTP_SERVER_PORT'):
    PORT = int(os.environ['HTTP_SERVER_PORT'])


os.chdir(os.environ["HTTP_ROOT_DIR"])


for ip in get_ip_addresses():
    print("http://%s:%i" % (ip, PORT))


# Copied from https://github.com/danvk/RangeHTTPServer/tree/ff4277417c6c8ea2435399659c25a172dbdfd24f


def copy_byte_range(infile, outfile, start=None, stop=None, bufsize=16 * 1024):
    """Like shutil.copyfileobj, but only copy a range of the streams.
    Both start and stop are inclusive.
    """
    if start is not None:
        infile.seek(start)
    while 1:
        to_read = min(bufsize, stop + 1 - infile.tell() if stop else bufsize)
        buf = infile.read(to_read)
        if not buf:
            break
        outfile.write(buf)


BYTE_RANGE_RE = re.compile(r"bytes=(\d+)-(\d+)?$")


def parse_byte_range(byte_range):
    """Returns the two numbers in 'bytes=123-456' or throws ValueError.
    The last number or both numbers may be None.
    """
    if byte_range.strip() == "":
        return None, None

    m = BYTE_RANGE_RE.match(byte_range)
    if not m:
        raise ValueError("Invalid byte range %s" % byte_range)

    first, last = [x and int(x) for x in m.groups()]
    if last and last < first:
        raise ValueError("Invalid byte range %s" % byte_range)
    return first, last


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Adds support for HTTP 'Range' requests to SimpleHTTPRequestHandler
    The approach is to:
    - Override send_head to look for 'Range' and respond appropriately.
    - Override copyfile to only transmit a range when requested.
    """

    def send_head(self):
        if "Range" not in self.headers:
            self.range = None
            return http.server.SimpleHTTPRequestHandler.send_head(self)
        try:
            self.range = parse_byte_range(self.headers["Range"])
        except ValueError as e:
            self.send_error(400, "Invalid byte range")
            return None
        first, last = self.range

        # Mirroring SimpleHTTPServer.py here
        path = self.translate_path(self.path)
        f = None
        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except IOError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs[6]
        if first >= file_len:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None

        self.send_response(206)
        self.send_header("Content-type", ctype)
        self.send_header("Accept-Ranges", "bytes")

        if last is None or last >= file_len:
            last = file_len - 1
        response_length = last - first + 1

        self.send_header("Content-Range", "bytes %s-%s/%s" % (first, last, file_len))
        self.send_header("Content-Length", str(response_length))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        if not self.range:
            return http.server.SimpleHTTPRequestHandler.copyfile(
                self, source, outputfile
            )

        # SimpleHTTPRequestHandler uses shutil.copyfileobj, which doesn't let
        # you stop the copying before the end of the file.
        start, stop = self.range  # set in send_head()
        copy_byte_range(source, outputfile, start, stop)


Handler = RangeRequestHandler
Handler.extensions_map.update({".mkv": "video/webm"})

with ThreadingHTTPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
