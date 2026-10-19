"""Command-line interface."""
import sys

from inventory.diff import compare
from inventory.loader import load_stock
from inventory.render import render_json, render_table

SCALE_TOLERANCE = 1  # the counting scale is only accurate to this many units


def main(argv):
    """Run the command line and return the exit status."""
    args = list(argv)
    as_json = "--json" in args
    paths = [a for a in args if a != "--json"]
    if len(paths) != 2:
        print("usage: python3 -m inventory [--json] OLD.json NEW.json", file=sys.stderr)
        return 2
    try:
        differences = compare(
            load_stock(paths[0]), load_stock(paths[1]), SCALE_TOLERANCE
        )
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    render = render_json if as_json else render_table
    for line in render(differences):
        print(line)
    return 0
