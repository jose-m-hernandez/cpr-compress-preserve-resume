"""Check a template file."""
import sys

from mailtpl.check import check_template


def main(argv):
    if len(argv) != 2 or argv[0] != "check":
        print("usage: python3 -m mailtpl check FILE", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        try:
            check_template(handle.read())
        except ValueError as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
    print("ok")
    return 0


raise SystemExit(main(sys.argv[1:]))
