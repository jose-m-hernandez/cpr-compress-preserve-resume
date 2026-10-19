"""Converting between dollar text and integer cents."""
import re

_AMOUNT = re.compile(r"([+-]?)(\d*)(?:\.(\d*))?")


def to_cents(text):
    """Convert dollar text such as '42.50' to integer cents.

    Raises ValueError if the text is not a number with at most two decimals.
    """
    match = _AMOUNT.fullmatch(text.strip())
    if not match:
        raise ValueError(f"bad amount {text!r}")
    sign, whole, fraction = match.group(1), match.group(2), match.group(3) or ""
    if not (whole or fraction) or len(fraction) > 2:
        raise ValueError(f"bad amount {text!r}")
    cents = int(whole or "0") * 100 + int(fraction.ljust(2, "0"))
    return -cents if sign == "-" else cents


def format_cents(cents):
    """Return integer cents as dollars and cents, e.g. 4250 -> '42.50'."""
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}{dollars}.{remainder:02d}"
