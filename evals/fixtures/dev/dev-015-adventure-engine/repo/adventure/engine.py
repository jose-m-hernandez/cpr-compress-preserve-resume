"""Running one command.

Commands: look, go DIRECTION, take ITEM, drop ITEM, save NAME, load NAME, quit.
"""

from adventure import saves

# Deprecated: "inspect" is an old spelling of "look". Remove it in version 2.
DEPRECATED_LOOK = "inspect"


def step(world, state, text):
    """Apply one command line to the state and return the message to show."""
    if state.finished:
        return "The game has ended."
    return _run_command(world, state, text)


def _run_command(world, state, text):
    """Apply the player's command to the state and return its message."""
    words = text.lower().split()
    if not words:
        return "Say something."
    if state.confirming_quit:
        state.confirming_quit = False
        if words[0] in ("yes", "y"):
            return _finish(state)
        if words[0] in ("no", "n"):
            return "Quit cancelled."
    if words == ["quit"]:
        return _quit(state)
    if words[0] in ("save", "load") and len(words) == 2:
        return _save_or_load(world, state, words[0], words[1])
    return _world_command(world, state, words)


def _quit(state):
    """Quit now, or ask first if there are moves since the last save."""
    if not state.unsaved:
        return _finish(state)
    state.confirming_quit = True
    return "Really quit? You have unsaved moves. (yes/no)"


def _finish(state):
    """End the game."""
    state.finished = True
    return "Goodbye."


def _world_command(world, state, words):
    """Run a command that acts on the rooms and return its message."""
    room = world["rooms"][state.room]
    if words[0] in ("look", DEPRECATED_LOOK):
        return room["description"]
    if words[0] == "go" and len(words) == 2:
        target = room.get("exits", {}).get(words[1])
        if target is None:
            return "You can't go that way."
        state.room = target
        state.unsaved = True
        return world["rooms"][target]["description"]
    if words[0] == "take" and len(words) == 2:
        if words[1] not in room.get("items", []):
            return f"There is no {words[1]} here."
        if state.inventory_full():
            return "Your hands are full."
        room["items"].remove(words[1])
        state.inventory.append(words[1])
        state.unsaved = True
        return f"You take the {words[1]}."
    if words[0] == "drop" and len(words) == 2:
        if words[1] not in state.inventory:
            return f"You aren't carrying a {words[1]}."
        state.inventory.remove(words[1])
        room.setdefault("items", []).append(words[1])
        state.unsaved = True
        return f"You drop the {words[1]}."
    return "I don't understand."


def _save_or_load(world, state, verb, name):
    """Run a save or load command and return its message."""
    action = saves.save_game if verb == "save" else saves.load_game
    try:
        action(world, state, name)
    except saves.SaveError as error:
        return str(error)
    state.unsaved = False
    done = "saved" if verb == "save" else "loaded"
    return f"Game {done}: {name}."
