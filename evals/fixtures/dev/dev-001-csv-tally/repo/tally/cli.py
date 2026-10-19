"""Command-line interface."""
import argparse

from tally.core import count_rows, load_rows, sum_column


def build_parser():
    parser = argparse.ArgumentParser(prog="tally", description="Sum a column of a CSV file.")
    parser.add_argument("file")
    parser.add_argument("--column")
    parser.add_argument("--count", action="store_true", help="print the number of rows instead of the sum")
    parser.add_argument("--delimiter", default=",", help="field delimiter (default: comma)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.count and args.column is None:
        parser.error("--column is required unless --count is given")
    rows = load_rows(args.file, args.delimiter)
    print(count_rows(rows) if args.count else sum_column(rows, args.column))
    return 0
