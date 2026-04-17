"""Servidor HTTP local para o dashboard Infosiga SP.

Uso: python analise/serve.py [porta]   (padrao 8000)
"""
from __future__ import annotations

import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in ("/favicon.ico", "/favicon.png"):
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()


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
