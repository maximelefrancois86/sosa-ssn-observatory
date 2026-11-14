#!/usr/bin/env python3
"""The static server of the SOSA/SSN Usage Observatory, inside its container.

    python3 -I serve.py --root /site --host 0.0.0.0 --port 8000

Serves the files of the public build (`make public`: the application and its data) read only,
with the media types the application needs (WebAssembly, JavaScript modules, a gzip graph
served as such), `/healthz` for the container's health check, and no directory listing.
Apache forwards https://ci.mines-stetienne.fr/sosa-ssn-observatory/ to it
(deploy/sosa-ssn-observatory.conf). Standard library only.
"""
import argparse
import http.server
import pathlib
import sys

CSP = ("connect-src 'self' https://cdn.jsdelivr.net; form-action 'self'; base-uri 'self'; "
       "frame-ancestors 'self'")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".json": "application/json", ".wasm": "application/wasm", ".gz": "application/gzip",
         ".ttl": "text/turtle; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
         ".ico": "image/x-icon", ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8",
         ".map": "application/json", ".woff2": "font/woff2", ".woff": "font/woff"}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **TYPES}

    def do_GET(self):
        if self.path == "/healthz":
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def list_directory(self, path):  # no listing
        self.send_error(404)
        return None

    def end_headers(self):
        # data change with each release; the browser asks again (304 when unchanged)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        # the pages may only send requests (fetch, XMLHttpRequest, WebSocket, beacons) to this
        # site and to the CDN of the SPARQL engine: neither Sparklis nor YASGUI can query
        # another endpoint, even from an edited address (Maxime, 2026-11-14)
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default="/site")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve()

    def handler(*args, **kw):
        return Handler(*args, directory=str(root), **kw)
    http.server.ThreadingHTTPServer((a.host, a.port), handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
