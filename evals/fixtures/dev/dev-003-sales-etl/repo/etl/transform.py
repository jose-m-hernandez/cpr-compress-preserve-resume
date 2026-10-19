"""Revenue calculations."""
import sys


def revenue_by_sku(sales):
    totals = {}
    skipped = 0
    for sale in sales:
        if sale["quantity"] < 0:
            skipped += 1
            continue
        totals[sale["sku"]] = totals.get(sale["sku"], 0.0) + sale["quantity"] * sale["unit_price"]
    if skipped:
        print(f"warning: {skipped} rows with negative quantity treated as returns and excluded", file=sys.stderr)
    return totals
