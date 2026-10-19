"""Remembering recently seen event ids."""
import threading
from collections import OrderedDict

CAPACITY = 5000


class SeenIds:
    """A thread-safe record of the most recent event ids."""

    def __init__(self, capacity=CAPACITY):
        self._capacity = capacity
        self._ids = OrderedDict()
        self._lock = threading.Lock()

    def claim(self, event_id):
        """Record an id; return False if it was already recorded."""
        with self._lock:
            if event_id in self._ids:
                return False
            self._ids[event_id] = None
            if len(self._ids) > self._capacity:
                self._ids.popitem(last=False)
            return True

    def release(self, event_id):
        """Forget an id so a retry of a failed event is processed again."""
        with self._lock:
            self._ids.pop(event_id, None)
