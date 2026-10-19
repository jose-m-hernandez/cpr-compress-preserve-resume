"""Formatting differences for output."""
import json


def render_table(differences):
    """Return the differences as plain table lines (going away after the next release)."""
    return [f"{d.sku:<10} {d.kind:<8} {d.old} -> {d.new}" for d in differences]


def render_json(differences):
    """Return one JSON object per difference, one per line."""
    return [json.dumps(d._asdict()) for d in differences]
