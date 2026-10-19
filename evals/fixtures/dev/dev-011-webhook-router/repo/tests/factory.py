"""Helpers for building test events."""
import itertools

_ids = itertools.count(1)


def make_event(type, **data):
    """Return a valid event dict of the given type; keyword args add or override fields."""
    event = {"id": f"evt_{next(_ids)}", "type": type, "sent": 100}
    event.update(data)
    return event
