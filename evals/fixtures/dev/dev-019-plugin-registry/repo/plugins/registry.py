"""The plugin registry."""

import re

_NAME_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


class PluginNotFound(KeyError):
    """Raised when no plugin is registered under the requested name."""


class Registry:
    """Maps names to plugin factories."""

    def __init__(self):
        self._factories = {}

    def register(self, name, factory):
        """Add a factory under a name.

        The name must be lowercase kebab-case, such as csv-export, and a
        repeated name is an error.
        """
        if not _NAME_PATTERN.fullmatch(name):
            raise ValueError(f"plugin name {name!r} must be lowercase kebab-case, such as 'csv-export'")
        if name in self._factories:
            raise ValueError(f"plugin {name!r} is already registered; the first registration is kept")
        self._factories[name] = factory

    def get(self, name):
        """Build and return the plugin called name; raise PluginNotFound if missing."""
        try:
            factory = self._factories[name]
        except KeyError:
            raise PluginNotFound(f"no plugin is registered as {name!r}") from None
        return factory()

    def names(self):
        """Return the registered names, sorted."""
        return sorted(self._factories)
