"""Reading a stock list: a JSON object mapping SKU to quantity."""
import json
import re

SKU_RE = re.compile(r"^[A-Z]+-[0-9]+$")


def load_stock(path):
    """Return {sku: quantity}, raising ValueError on a bad entry."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    for sku, quantity in data.items():
        if not SKU_RE.match(sku):
            raise ValueError(f"sku {sku!r} is not valid; skus are upper-case letters, a dash and digits")
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError(f"quantity for {sku} must be a whole number of zero or more")
    return data
