"""Command-line entry point."""
import sys

from etl.load import load_sales
from etl.transform import revenue_by_sku


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    totals = revenue_by_sku(load_sales(args[0]))
    for sku in sorted(totals):
        print(f"{sku}\t{totals[sku]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
