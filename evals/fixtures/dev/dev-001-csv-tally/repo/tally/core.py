"""Reading rows and summing a column."""
import csv


def load_rows(path: str, delimiter: str = ",") -> list:
    """Return the rows of a CSV file as a list of dicts."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def parse_number(text, column, row):
    """Convert one cell to a float, naming the column and row on failure."""
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"bad number {text!r} in column {column!r} (row {row}); decimals must use '.'")


def sum_column(rows, column):
    """Add up one column; row numbers count the header as row 1."""
    total = 0.0
    for index, row in enumerate(rows, start=2):
        total += parse_number(row[column], column, index)
    return total


def count_rows(rows: list) -> int:
    """Count the data rows, not including the header."""
    return len(rows)
