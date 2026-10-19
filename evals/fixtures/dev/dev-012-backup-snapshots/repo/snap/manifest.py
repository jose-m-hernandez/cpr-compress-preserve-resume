"""Writing a manifest of the files in a snapshot."""
import json
import os

MANIFEST_NAME = "MANIFEST.json"


def build_manifest(root):
    """Return a list of {"path", "size"} entries for files under root, sorted by path."""
    entries = []
    for folder, _dirs, files in os.walk(root):
        for name in files:
            full = os.path.join(folder, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            entries.append({"path": rel, "size": os.path.getsize(full)})
    return sorted(entries, key=lambda entry: entry["path"])


def write_manifest(root):
    """Write MANIFEST.json into root, listing every file except itself, and return its path."""
    path = os.path.join(root, MANIFEST_NAME)
    files = build_manifest(root)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"files": files}, handle, indent=2)
        handle.write("\n")
    return path
