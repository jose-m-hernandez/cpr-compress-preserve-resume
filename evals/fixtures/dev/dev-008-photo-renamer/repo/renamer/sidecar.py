"""Reading the sidecar file."""
from collections import namedtuple

Record = namedtuple("Record", "old date title")


def parse_sidecar(text):
    """Parse lines shaped `OLD | DATE | TITLE` into records."""
    records = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3:
            raise ValueError(f"sidecar line {number}: expected 3 fields")
        records.append(Record(*parts))
    return records
