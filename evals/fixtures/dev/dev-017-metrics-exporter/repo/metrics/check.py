"""Checking metric names: each line is `KIND NAME`."""

from metrics.registry import validate_name


def check_names(lines):
    """Raise ValueError for the first bad line."""
    for number, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"line {number}: expected KIND NAME")
        kind, name = parts
        try:
            validate_name(name)
        except ValueError as error:
            raise ValueError(f"line {number}: {error}") from None
        if kind == "counter" and not name.endswith("_total"):
            raise ValueError(f"line {number}: counter names must end in _total")
