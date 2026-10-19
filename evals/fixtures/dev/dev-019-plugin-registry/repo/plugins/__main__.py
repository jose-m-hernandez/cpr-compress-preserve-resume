"""Register the names in a file and report problems."""
import sys

from plugins.registry import Registry


def main(argv):
    if len(argv) != 2 or argv[0] != "check":
        print("usage: python3 -m plugins check FILE", file=sys.stderr)
        return 2
    registry = Registry()
    with open(argv[1], encoding="utf-8") as handle:
        names = [line.strip() for line in handle if line.strip()]
    try:
        for name in names:
            registry.register(name, object)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"ok: {len(names)} plugins")
    return 0


raise SystemExit(main(sys.argv[1:]))
