"""Reading the flag file."""
import json


def load_flags(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
