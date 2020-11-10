import http.server
import socketserver
import os

os.chdir(r'{{_DIR}}' if r'{{_DIR}}' else os.environ['CUR_DIR_'])

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map.update({'.mkv': 'video/webm'})

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
