"""Loading and checking a world file."""
import json


def validate_world(world):
    """Raise ValueError if the world is not usable."""
    rooms = world.get("rooms", {})
    if world.get("start") not in rooms:
        raise ValueError("the start room does not exist")
    for name, room in rooms.items():
        for direction, target in room.get("exits", {}).items():
            if target not in rooms:
                raise ValueError(f"room {name!r} has an exit to unknown room {target!r}; every exit must name an existing room")


def load_world(path):
    """Read a world file and check it."""
    with open(path, encoding="utf-8") as handle:
        world = json.load(handle)
    validate_world(world)
    return world
