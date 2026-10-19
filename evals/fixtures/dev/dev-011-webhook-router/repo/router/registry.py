"""Mapping event types to handlers."""
from router.handlers import all_handlers


class Registry:
    """Holds one handler per event type."""

    def __init__(self):
        self._handlers = {}

    def register(self, event_type, handler):
        """Attach a handler (a function taking the event) to a type."""
        self._handlers[event_type] = handler

    def get(self, event_type):
        """Return the handler for a type, or None."""
        return self._handlers.get(event_type)


def default_registry():
    """Return the registry the service starts with."""
    registry = Registry()
    registry.register("ping", lambda event: None)
    for event_type, handler in all_handlers().items():
        registry.register(event_type, handler)
    return registry
