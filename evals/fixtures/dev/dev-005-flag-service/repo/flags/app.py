"""HTTP layer."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from flags.store import FlagStore

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = FlagStore(os.path.join(HERE, "..", "config", "flags.json"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/flags/"):
            self.send_error(404)
            return
        name = self.path[len("/flags/"):]
        try:
            payload = {"enabled": STORE.evaluate(name)}
            status = 200
        except KeyError:
            payload, status = {"error": "unknown flag"}, 404
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8090), Handler).serve_forever()
