import http.server
import os
import socketserver

from _shutil import get_files, get_ip_addresses

from md_to_html import convert_md_to_html

if __name__ == "__main__":
    ip_addresses = get_ip_addresses()
    port = 9527

    in_file = get_files(cd=True)[0]
    out_file = convert_md_to_html(in_file)

    with socketserver.TCPServer(
        ("", port), http.server.SimpleHTTPRequestHandler
    ) as httpd:
        for ip in ip_addresses:
            print(f"http://{ip}:{port}/" + os.path.basename(out_file))
        httpd.serve_forever()
