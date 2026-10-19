"""A tiny time-based cache."""
import time

TTL_SECONDS = 30


class TTLCache:
    def __init__(self, ttl=TTL_SECONDS, clock=time.monotonic):
        self.ttl = ttl
        self.clock = clock
        self.entries = {}

    def get(self, key):
        entry = self.entries.get(key)
        if entry and self.clock() - entry[1] < self.ttl:
            return entry[0]
        return None

    def put(self, key, value):
        self.entries[key] = (value, self.clock())
