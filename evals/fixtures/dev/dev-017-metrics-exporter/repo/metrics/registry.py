"""Counters held in memory."""

import re

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def validate_name(name):
    """Raise ValueError unless name is letters, digits and underscores.

    Labels are not supported, so braces, quotes and spaces are rejected;
    put each dimension in the name, joined with underscores.
    """
    if not _NAME.fullmatch(name):
        raise ValueError(f"invalid metric name: {name!r}")


class Counter:
    """A value that only goes up."""

    def __init__(self, name):
        self.name = name
        self.value = 0

    def add(self, n):
        """Add n, which must not be negative."""
        if n < 0:
            raise ValueError("counters only go up")
        self.value += n

    def inc(self):
        """Add one."""
        self.value += 1


class Registry:
    """Holds counters by name."""

    def __init__(self):
        self._counters = {}

    def counter(self, name):
        """Return the counter called name, creating it if needed."""
        if name not in self._counters:
            validate_name(name)
            self._counters[name] = Counter(name)
        return self._counters[name]

    def counters(self):
        """Return all counters sorted by name."""
        return [self._counters[name] for name in sorted(self._counters)]
