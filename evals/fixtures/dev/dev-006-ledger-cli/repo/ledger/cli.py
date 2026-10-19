"""Command-line interface."""
import argparse
import datetime
import os
import sys

from ledger.parse import parse_file
from ledger.report import format_report
from ledger.summary import GROUPINGS, since, top_totals, totals_by


DEFAULT_FILE = os.path.join("data", "ledger.txt")


def resolve_path(path):
    """Pick the ledger file: the argument, else $LEDGER_FILE, else the default."""
    return path or os.environ.get("LEDGER_FILE") or DEFAULT_FILE


def positive_int(text):
    """Argparse type for a whole number of at least 1."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid number {text!r}")
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def iso_date(text):
    """Argparse type for a YYYY-MM-DD date."""
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {text!r}; use YYYY-MM-DD")
    return text


def build_parser():
    parser = argparse.ArgumentParser(prog="ledger", description="Summarise an expense ledger.")
    parser.add_argument("file", nargs="?",
                        help=f"ledger file (default: $LEDGER_FILE, else {DEFAULT_FILE})")
    parser.add_argument("--by", choices=sorted(GROUPINGS), default="month",
                        help="how to group the totals (default: month; weeks are labelled by their Monday)")
    parser.add_argument("--top", type=positive_int, default=3, metavar="N",
                        help="show only the N biggest groups by total (default: 3)")
    parser.add_argument("--since", type=iso_date, metavar="YYYY-MM-DD",
                        help="skip entries dated before this day")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        entries = parse_file(resolve_path(args.file))
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    if args.since:
        entries = since(entries, args.since)
    print(format_report(top_totals(totals_by(entries, args.by), args.top)))
    return 0
