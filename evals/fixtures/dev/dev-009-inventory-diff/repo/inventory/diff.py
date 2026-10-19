"""Comparing two stock lists."""
from collections import namedtuple

Difference = namedtuple("Difference", "sku kind old new")


def compare(old, new, tolerance=0):
    """Return the differences between two {sku: quantity} dicts, sorted by SKU.

    Quantity changes of `tolerance` units or less are ignored.
    """
    out = []
    for sku in sorted(set(old) | set(new)):
        if sku not in old:
            out.append(Difference(sku, "added", None, new[sku]))
        elif sku not in new:
            out.append(Difference(sku, "removed", old[sku], None))
        elif abs(new[sku] - old[sku]) > tolerance:
            out.append(Difference(sku, "changed", old[sku], new[sku]))
    return out
