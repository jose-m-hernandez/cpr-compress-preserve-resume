"""Defining and evaluating flags."""
import json

from flags.cache import TTLCache
from flags.loader import load_flags
from flags.validate import check_name


class FlagStore:
    def __init__(self, path):
        self.path = path
        self.cache = TTLCache()

    def define(self, name, enabled):
        check_name(name)
        flags = load_flags(self.path)
        flags[name] = bool(enabled)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(flags, handle)

    def evaluate(self, name):
        cached = self.cache.get(name)
        if cached is not None:
            return cached
        flags = load_flags(self.path)
        if name not in flags:
            return False
        value = flags[name]
        self.cache.put(name, value)
        return value
