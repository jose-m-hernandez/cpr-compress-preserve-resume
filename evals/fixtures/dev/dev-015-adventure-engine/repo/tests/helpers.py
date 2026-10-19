import copy

from adventure.engine import step
from adventure.state import GameState


def play(world, commands):
    """Run command strings in a fresh game and return the list of messages.

    The world is copied first, so a test never changes the world it passed in.
    The game starts in world["start"].
    """
    world = copy.deepcopy(world)
    state = GameState(world["start"])
    return [step(world, state, command) for command in commands]
