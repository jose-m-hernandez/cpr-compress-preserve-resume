"""Replay a saved event through the router."""
import json
import sys

from router.dispatch import dispatch
from router.registry import default_registry


def main(argv):
    if len(argv) != 2 or argv[0] != "replay":
        print("usage: python3 -m router replay FILE", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        status, payload = dispatch(handle.read(), default_registry())
    print(status, json.dumps(payload))
    return 0 if status == 200 else 1


raise SystemExit(main(sys.argv[1:]))
