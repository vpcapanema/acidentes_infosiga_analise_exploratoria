"""Servidor HTTP local para o dashboard Infosiga SP.

Uso: python analise/serve.py [porta]   (padrao 8000)
"""
from __future__ import annotations

import gzip
import io
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


class Handler(SimpleHTTPRequestHandler):
    compressible_types = (
        "text/html",
        "text/css",
        "application/javascript",
        "text/javascript",
        "application/json",
        "text/plain",
        "image/svg+xml",
    )

    def do_GET(self):  # noqa: N802
        if self.path in ("/favicon.ico", "/favicon.png"):
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_file():
            ctype = self.guess_type(str(path))
            accepts_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
            if accepts_gzip and any(ctype.startswith(prefix) for prefix in self.compressible_types):
                raw = path.read_bytes()
                payload = gzip.compress(raw, compresslevel=6)
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Vary", "Accept-Encoding")
                self.end_headers()
                return io.BytesIO(payload)
        return super().send_head()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = partial(Handler, directory=str(DOCS))
    url = f"http://localhost:{port}/index.html"
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Servindo {DOCS} em {url}")
        print("Ctrl+C para encerrar.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nEncerrado.")


if __name__ == "__main__":
    main()
