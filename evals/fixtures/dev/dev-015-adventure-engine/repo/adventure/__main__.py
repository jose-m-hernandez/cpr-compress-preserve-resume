"""Validate a world file."""
import sys

from adventure.world import load_world


def main(argv):
    if len(argv) != 2 or argv[0] != "check":
        print("usage: python3 -m adventure check FILE", file=sys.stderr)
        return 2
    try:
        world = load_world(argv[1])
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"ok: {len(world['rooms'])} rooms")
    return 0


raise SystemExit(main(sys.argv[1:]))
