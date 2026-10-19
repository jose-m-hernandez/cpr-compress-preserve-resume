"""HTTP layer for the notes service."""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from notes_api.store import NoteStore

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = None


def load_config():
    with open(os.path.join(HERE, "..", "config.json"), encoding="utf-8") as handle:
        return json.load(handle)


def list_notes():
    return 200, {"notes": STORE.notes}


def get_note(note_id):
    note = STORE.find(int(note_id))
    if note is None:
        return 404, {"error": "not found"}
    return 200, {"id": int(note_id), **note}


def delete_note(note_id):
    if not STORE.delete(int(note_id)):
        return 404, {"error": "not found"}
    return 200, {"id": int(note_id), "deleted": True}


ROUTES = [
    ("GET", r"/v1/notes", list_notes),
    ("GET", r"/v2/notes/(\d+)", get_note),
    ("DELETE", r"/v2/notes/(\d+)", delete_note),
]


def dispatch(method, path):
    for route_method, pattern, func in ROUTES:
        match = re.fullmatch(pattern, path)
        if route_method == method and match:
            return func, match.groups()
    return None, ()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond("GET")

    def do_DELETE(self):
        self.respond("DELETE")

    def respond(self, method):
        func, groups = dispatch(method, self.path)
        status, payload = func(*groups) if func else (404, {"error": "not found"})
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve():
    global STORE
    config = load_config()
    STORE = NoteStore(config["data_file"])
    HTTPServer(("127.0.0.1", config["port"]), Handler).serve_forever()


if __name__ == "__main__":
    serve()
