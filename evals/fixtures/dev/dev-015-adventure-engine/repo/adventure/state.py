"""The player's state."""


INVENTORY_LIMIT = 6


class GameState:
    """Where the player is and what they carry."""

    def __init__(self, room):
        self.room = room
        self.inventory = []
        self.unsaved = False
        self.confirming_quit = False
        self.finished = False

    def inventory_full(self):
        """Return True if the player cannot carry anything more."""
        return len(self.inventory) >= INVENTORY_LIMIT
