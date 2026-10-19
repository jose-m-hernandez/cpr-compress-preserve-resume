"""Command-line interface."""
import os
import sys

from renamer.plan import apply_plan, make_plan
from renamer.sidecar import parse_sidecar

USAGE = "usage: python3 -m renamer plan DIR | python3 -m renamer apply DIR --yes"


def load_plan(directory):
    """Read DIR/index.txt and return its plan."""
    with open(os.path.join(directory, "index.txt"), encoding="utf-8") as handle:
        return make_plan(parse_sidecar(handle.read()))


def main(argv):
    if len(argv) == 2 and argv[0] == "plan":
        command, directory = argv
    elif len(argv) == 3 and argv[0] == "apply" and "--yes" in argv[1:]:
        command, directory = argv[0], next(a for a in argv[1:] if a != "--yes")
    elif argv[:1] == ["apply"]:
        print("error: apply renames files for real; pass --yes to confirm", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    else:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        plan = load_plan(directory)
        if command == "apply":
            apply_plan(directory, plan)
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    for old, new in plan:
        print(f"{old} -> {new}")
    return 0
