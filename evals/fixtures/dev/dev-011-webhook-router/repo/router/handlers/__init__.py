"""Event handlers, one module per event family."""
from router.handlers import orders

FAMILIES = (orders,)


def all_handlers():
    """Return a dict of every event type to its handler."""
    handlers = {}
    for family in FAMILIES:
        handlers.update(family.HANDLERS)
    return handlers
