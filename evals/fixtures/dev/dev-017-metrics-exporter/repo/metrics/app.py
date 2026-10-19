"""Serve the registry at /-/metrics."""

from metrics.registry import Registry
from metrics.render import render

REGISTRY = Registry()


def handle(path, registry=None):
    """Return (status, body) for a request path."""
    if path == "/-/metrics":
        return 200, render(REGISTRY if registry is None else registry)
    return 404, "not found\n"
