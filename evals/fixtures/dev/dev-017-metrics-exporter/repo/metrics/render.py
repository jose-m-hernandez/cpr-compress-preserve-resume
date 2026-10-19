"""Render a registry as plain text."""


def render(registry):
    """Return one "name value" line per counter, sorted by name."""
    return "".join(f"{c.name} {c.value}\n" for c in registry.counters())
