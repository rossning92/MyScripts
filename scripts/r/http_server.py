import http.server
import socketserver
import os

os.chdir(os.path.expanduser('~/Desktop'))

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map.update({'.mkv': 'video/webm'})

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
