"""Local browser app. AI assistance: Codex helped implement this study tool."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import webbrowser

import numpy as np
import pandas as pd
import io

from analysis import analyze


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/":
            self.reply(404, b'{}')
            return
        self.reply(200, Path(__file__).with_name("index.html").read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 5_000_000:
                raise ValueError("Request must be less than 5 MB.")
            request = json.loads(self.rfile.read(size))
            if self.path == "/columns":
                frame = pd.read_csv(io.StringIO(request.get("csv", "")))
                result = {"columns": list(frame.columns), "values": {
                    c: frame[c].dropna().astype(str).str.strip().unique()[:30].tolist() for c in frame}}
            elif self.path == "/analyze":
                result = analyze(request)
            else:
                self.reply(404, b'{}')
                return
            body = json.dumps(result, default=lambda v: v.item() if isinstance(v, np.generic) else v,
                              allow_nan=False).encode()
            self.reply(200, body)
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            self.reply(400, json.dumps({"error": str(error)}).encode())

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        server = HTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        server = HTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Statistical Inference Lab: {url}\nPress Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
