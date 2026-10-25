#!/usr/bin/env python3
"""Local-only UI preview for DoppleJa. No database or authentication access."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / 'frontend'
PREVIEW = Path(__file__).resolve().parent / 'ui_preview'

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ('/', '/preview', '/preview.html'):
            target = PREVIEW / 'index.html'
        elif path.startswith('/app-assets/'):
            target = FRONTEND / path[len('/app-assets/'):]
        else:
            self.send_error(404, 'Preview only'); return
        target = target.resolve()
        base = (PREVIEW if path in ('/', '/preview', '/preview.html') else FRONTEND).resolve()
        if not target.is_file() or not target.is_relative_to(base):
            self.send_error(404, 'Asset not found'); return
        import mimetypes
        content = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors 'self'")
        self.end_headers(); self.wfile.write(content)

    def do_POST(self): self.send_error(405, 'Read-only preview')
    def do_PUT(self): self.send_error(405, 'Read-only preview')
    def do_DELETE(self): self.send_error(405, 'Read-only preview')
    def log_message(self, fmt, *args): pass

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='DoppleJa local-only UI preview')
    ap.add_argument('--port', type=int, default=8765)
    args = ap.parse_args()
    if not FRONTEND.is_dir(): raise SystemExit('Run this from the extracted DoppleJa project, with frontend/ present')
    with ThreadingHTTPServer(('127.0.0.1',args.port), Handler) as server:
        print(f'Local preview: http://127.0.0.1:{args.port}/preview')
        print('Press Ctrl+C to stop. Localhost only, no database or login.')
        try:server.serve_forever()
        except KeyboardInterrupt:pass
