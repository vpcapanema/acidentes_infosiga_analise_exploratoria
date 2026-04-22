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
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def end_headers(self):
        # HTML e JSON sao recursos dinamicos do dashboard e nao devem ser cacheados
        # pelo navegador, sob pena de o usuario ver conteudo desatualizado apos
        # qualquer regeneracao de dados ou edicao da pagina.
        path = self.path.split('?')[0].lower()
        if path.endswith('.html') or path.endswith('.json') or path == '/' or path.endswith('/'):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_file():
            ctype = self.guess_type(str(path))
            accept_encoding = self.headers.get("Accept-Encoding", "")
            accepts_br = "br" in accept_encoding
            accepts_gzip = "gzip" in accept_encoding
            # Prefer precompressed assets when available.
            if accepts_br and path.suffix in {".json", ".js", ".css", ".html"}:
                br_path = path.with_suffix(path.suffix + ".br")
                # Usa o precompressed apenas se ele for mais novo que o original.
                # Caso contrario serve o original (gzip on-the-fly) para evitar
                # entregar conteudo defasado quando o autor edita o html/json.
                if br_path.is_file() and br_path.stat().st_mtime >= path.stat().st_mtime:
                    payload = br_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-type", ctype)
                    self.send_header("Content-Encoding", "br")
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Vary", "Accept-Encoding")
                    self.end_headers()
                    return io.BytesIO(payload)
            if accepts_gzip and path.suffix in {".json", ".js", ".css", ".html"}:
                gz_path = path.with_suffix(path.suffix + ".gz")
                if gz_path.is_file() and gz_path.stat().st_mtime >= path.stat().st_mtime:
                    payload = gz_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-type", ctype)
                    self.send_header("Content-Encoding", "gzip")
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Vary", "Accept-Encoding")
                    self.end_headers()
                    return io.BytesIO(payload)
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
