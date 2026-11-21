#!/usr/bin/env python3
"""Minimal health server for the CI-session reachability spike.

Stdlib only. Listens on 0.0.0.0:8765 (override with PORT).
GET /health -> 200 {"status": "ok", "hostname": ..., "time": ...}
Any other path -> 200 plain text identifying the spike server.
"""
import json
import os
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (stdlib naming)
        if self.path == "/health":
            body = json.dumps({
                "status": "ok",
                "hostname": socket.gethostname(),
                "time": datetime.now(timezone.utc).isoformat(),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            body = b"android-ci spike server\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
