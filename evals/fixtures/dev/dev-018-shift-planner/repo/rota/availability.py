"""Reading availability: one line per person, `NAME: day, day, ...`."""

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def parse_availability(text):
    """Return {name: set of days}."""
    people = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        name, _, rest = line.partition(":")
        days = {day.strip() for day in rest.split(",") if day.strip()}
        for day in sorted(days):
            if day not in DAYS:
                raise ValueError(f"line {number}: unknown day {day!r}; days are written mon, tue, wed, thu, fri, sat, sun")
        people[name.strip()] = days
    return people
