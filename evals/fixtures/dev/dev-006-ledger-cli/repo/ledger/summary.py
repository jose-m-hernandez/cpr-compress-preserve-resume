"""Totals for the report."""
import datetime


def since(entries, start):
    """Keep only entries dated on or after `start` (an ISO date string)."""
    return [entry for entry in entries if entry.date >= start]


def week_start(date_text):
    """Return the ISO date of the Monday on or before the given ISO date."""
    day = datetime.date.fromisoformat(date_text)
    return (day - datetime.timedelta(days=day.weekday())).isoformat()


GROUPINGS = {
    "category": lambda entry: entry.category,
    "week": lambda entry: week_start(entry.date),
    "month": lambda entry: entry.date[:7],
}


def totals_by(entries, by):
    """Add up the amounts of each group, in integer cents.

    `by` is a key of GROUPINGS: "category", "week" (labelled by its Monday),
    or "month" (labelled YYYY-MM).
    """
    key = GROUPINGS[by]
    totals = {}
    for entry in entries:
        totals[key(entry)] = totals.get(key(entry), 0) + entry.amount
    return totals


def totals_by_category(entries):
    """Add up the amounts of each category, in integer cents."""
    return totals_by(entries, "category")


def top_totals(totals, count):
    """Keep the `count` groups with the largest totals; ties go by name."""
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return dict(ranked[:count])
