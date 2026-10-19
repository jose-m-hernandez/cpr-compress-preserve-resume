"""Reading ledger lines."""
import datetime
from collections import namedtuple

from ledger.money import to_cents

Entry = namedtuple("Entry", "date description amount category")


def parse_amount(text, number):
    """Convert one amount cell to integer cents."""
    try:
        value = to_cents(text)
    except ValueError:
        raise ValueError(f"line {number}: bad amount {text!r}")
    if value < 0:
        raise ValueError(f"line {number}: amounts must be positive; refunds go under category 'refund', never as a negative amount")
    return value


def parse_line(line, number):
    """Turn one ledger line into an Entry."""
    parts = [part.strip() for part in line.split("|")]
    if len(parts) != 4:
        raise ValueError(f"line {number}: expected 4 fields, found {len(parts)}")
    date, description, amount, category = parts
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError(f"line {number}: bad date {date!r}")
    return Entry(date, description, parse_amount(amount, number), category.lower())


def parse_file(path):
    """Read every entry in a ledger file."""
    entries = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            text = line.strip()
            if text and not text.startswith("#"):
                entries.append(parse_line(text, number))
    return entries
