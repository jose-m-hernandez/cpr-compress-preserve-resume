"""Saving and loading the game as JSON files."""

import json
import os
import re

SAVE_DIR = "saves"


class SaveError(Exception):
    """A save or load could not be done; the message is fit to show."""


def save_path(name):
    """Return the file path for save NAME, rejecting unsafe names."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise SaveError("Save names may only use letters, digits, - and _.")
    return os.path.join(SAVE_DIR, name + ".json")


def snapshot(world, state):
    """Return the game state as a JSON-ready dict."""
    items = {name: list(room.get("items", []))
             for name, room in world["rooms"].items()}
    return {"room": state.room, "inventory": list(state.inventory),
            "items": items}


def save_game(world, state, name):
    """Write the current game to saves/NAME.json."""
    path = save_path(name)
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(path, "w") as handle:
        json.dump(snapshot(world, state), handle, indent=2)


def read_save(name):
    """Return the dict stored in saves/NAME.json."""
    try:
        with open(save_path(name)) as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SaveError(f"No save called {name}.")
    except ValueError:
        raise SaveError(f"The save {name} is damaged.")


def load_game(world, state, name):
    """Restore the game from saves/NAME.json into `world` and `state`."""
    data = read_save(name)
    try:
        rooms = world["rooms"]
        if data["room"] not in rooms:
            raise SaveError(f"The save {name} does not fit this world.")
        room, inventory = data["room"], list(data["inventory"])
        items = data["items"]
        for room_name, held in items.items():
            if room_name not in rooms:
                raise SaveError(f"The save {name} does not fit this world.")
    except (KeyError, TypeError, AttributeError):
        raise SaveError(f"The save {name} is damaged.")
    for room_name, held in items.items():
        rooms[room_name]["items"] = list(held)
    state.room, state.inventory = room, inventory
