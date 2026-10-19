"""The printed report."""
from ledger.money import format_cents


def format_report(totals):
    """Return one aligned line per category, sorted by name."""
    width = max((len(name) for name in totals), default=0)
    return "\n".join(f"{name.ljust(width)}  {format_cents(total):>9}" for name, total in sorted(totals.items()))
