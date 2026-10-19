"""Command-line entry point."""
import sys

from shortener.urls import check_url


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "check":
        print("usage: python3 -m shortener check URL", file=sys.stderr)
        return 2
    try:
        print("ok:", check_url(argv[1]))
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


raise SystemExit(main())
