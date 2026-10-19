"""Writing the revenue report to disk."""
import os


def write_report(totals, month, out_dir="out"):
    """Write totals to <out_dir>/report_<month>.txt and return the path.

    `month` is a "YYYY-MM" string. Output matches the command-line report:
    one tab-separated line per SKU, rounded to cents here and nowhere earlier.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"report_{month}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        for sku in sorted(totals):
            handle.write(f"{sku}\t{totals[sku]:.2f}\n")
    return path
