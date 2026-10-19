"""Command-line entry point."""
import sys

from units.convert import convert


def main(argv):
    if len(argv) != 3:
        print("usage: python3 -m units VALUE FROM TO", file=sys.stderr)
        return 2
    try:
        print(convert(float(argv[0]), argv[1], argv[2]))
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


raise SystemExit(main(sys.argv[1:]))
