"""The undo log that lets an apply be reversed."""
import json
import os

LOG_NAME = ".renamer-undo.json"


def read_log(directory):
    """Return the logged renames as a list of old/new dicts; empty if there is no log."""
    try:
        with open(os.path.join(directory, LOG_NAME), encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return []


def write_log(directory, plan):
    """Append one entry per (old, new) pair to the log, keeping earlier entries."""
    entries = read_log(directory)
    entries.extend(dict(old=old, new=new) for old, new in plan)
    with open(os.path.join(directory, LOG_NAME), "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)
