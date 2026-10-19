"""Print the fields of an expression."""
import sys

from cronish.parser import parse


def main(argv):
    if len(argv) != 1:
        print("usage: python3 -m cronish 'MINUTE HOUR WEEKDAY'", file=sys.stderr)
        return 2
    try:
        schedule = parse(argv[0])
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print("minutes:", sorted(schedule.minutes))
    print("hours:", sorted(schedule.hours))
    print("weekdays:", sorted(schedule.weekdays))
    return 0


raise SystemExit(main(sys.argv[1:]))
