#!/usr/bin/env python3
"""Simple file server for State Electric project files over Tailscale."""
import http.server
import os
from pathlib import Path
from urllib.parse import unquote

SHARE_DIR = Path(__file__).parent.resolve()

class CustomHandler(http.server.BaseHTTPRequestHandler):
    server_version = "StateElectric/1.0"
    
    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header('Location', self.path + '/')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            self.list_directory(path)
        elif os.path.isfile(path):
            self.serve_file(path)
        else:
            self.send_error(404, "File not found")
    
    def serve_file(self, path):
        import mimetypes
        ctype, _ = mimetypes.guess_type(path)
        if ctype is None:
            ctype = 'application/octet-stream'
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError:
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)
    
    def translate_path(self, path):
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = unquote(path)
        words = path.split('/')
        words = [w for w in words if w and w != '..']
        return str(SHARE_DIR / '/'.join(words))
    
    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

class ReusableServer(http.server.HTTPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    os.chdir(SHARE_DIR)
    port = 8765
    server = ReusableServer(('0.0.0.0', port), CustomHandler)
    print(f"State Electric File Server running on port {port}")
    server.serve_forever()
