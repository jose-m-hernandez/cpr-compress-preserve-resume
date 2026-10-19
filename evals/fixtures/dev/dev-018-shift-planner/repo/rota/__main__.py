"""Print the rota for an availability file."""
import sys

from rota.availability import DAYS, parse_availability
from rota.planner import assign


def main(argv):
    if len(argv) != 1:
        print("usage: python3 -m rota AVAILABILITY_FILE", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as handle:
            people = parse_availability(handle.read())
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    rota = assign(people)
    for day in DAYS:
        print(f"{day}: {', '.join(rota[day])}")
    return 0


raise SystemExit(main(sys.argv[1:]))
