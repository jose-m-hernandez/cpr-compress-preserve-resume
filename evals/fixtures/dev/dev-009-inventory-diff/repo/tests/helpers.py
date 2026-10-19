"""Shared test setup: inventories are built in code, never read from data/."""
import json
import os
import tempfile

from inventory.diff import Difference


def write_stock(test, data):
    """Write `data` to a temporary JSON stock list and return its path.

    The file is deleted when `test` finishes.
    """
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    test.addCleanup(os.unlink, handle.name)
    json.dump(data, handle)
    handle.close()
    return handle.name


def sample_differences():
    """Return one changed and one added difference."""
    return [Difference("A-1", "changed", 1, 9), Difference("B-1", "added", None, 3)]
