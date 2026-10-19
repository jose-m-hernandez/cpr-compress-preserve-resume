"""Parsing schedule expressions."""
from collections import namedtuple

from cronish.errors import ExprError

Schedule = namedtuple("Schedule", "minutes hours weekdays")


def parse_int(text, name, kind=""):
    """Convert text to an int, raising ExprError that names the field on failure."""
    try:
        return int(text)
    except ValueError:
        raise ExprError(f"{name} {kind}{text!r} is not a number") from None


def parse_step(text, name):
    """Convert a step to a positive int."""
    step = parse_int(text, name, "step ")
    if step < 1:
        raise ExprError(f"{name} step {text!r} must be at least 1")
    return step


def parse_field(text, low, high, name):
    """Expand one field (`*`, `N`, `A-B`, `*/N` or a comma list) into a set of ints.

    Raises ExprError, with the field name in the message, on bad input.
    """
    values = set()
    for part in text.split(","):
        step = 1
        if "/" in part:
            part, step_text = part.split("/", 1)
            step = parse_step(step_text, name)
        if part == "*":
            start, end = low, high
        elif "-" in part:
            start, end = (parse_int(x, name) for x in part.split("-", 1))
        else:
            start = end = parse_int(part, name)
        if name == "weekday" and end == 7:
            raise ExprError("weekday 7 is not accepted; Sunday is 0")
        if start < low or end > high or start > end:
            raise ExprError(f"{name} {part!r} is out of range {low}-{high}")
        values.update(range(start, end + 1, step))
    return values


def parse(expr):
    """Parse `MINUTE HOUR WEEKDAY` into a Schedule."""
    fields = expr.split()
    if len(fields) != 3:
        raise ExprError(f"expected 3 fields (minute hour weekday), found {len(fields)}")
    return Schedule(parse_field(fields[0], 0, 59, "minute"),
                    parse_field(fields[1], 0, 23, "hour"),
                    parse_field(fields[2], 0, 6, "weekday"))
