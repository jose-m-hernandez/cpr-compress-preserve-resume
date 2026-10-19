"""Turning records into renames."""
import os
import re

from renamer.undo import write_log

SLUG_MAX = 30


def slugify(title):
    """Lowercase title with hyphens between words, cut to SLUG_MAX characters."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:SLUG_MAX].rstrip("-")


def new_name(record):
    """Build the new file name for one record."""
    ext = os.path.splitext(record.old)[1]
    return f"{record.date}_{slugify(record.title)}{ext}"


def make_plan(records):
    """Return (old, new) pairs sorted by old name; refuse two files with one target."""
    seen = {}
    plan = []
    for record in sorted(records, key=lambda r: r.old):
        new = new_name(record)
        if new in seen:
            raise ValueError(f"{seen[new]} and {record.old} would both become {new}")
        seen[new] = record.old
        plan.append((record.old, new))
    return plan


def apply_plan(directory, plan):
    """Rename files in directory per plan; check everything first so a bad plan changes nothing.

    The undo log is written after the checks and before the first rename.
    """
    for old, new in plan:
        if not os.path.isfile(os.path.join(directory, old)):
            raise ValueError(f"{old} does not exist")
        if os.path.lexists(os.path.join(directory, new)):
            raise ValueError(f"{new} already exists")
    write_log(directory, plan)
    for old, new in plan:
        os.rename(os.path.join(directory, old), os.path.join(directory, new))
