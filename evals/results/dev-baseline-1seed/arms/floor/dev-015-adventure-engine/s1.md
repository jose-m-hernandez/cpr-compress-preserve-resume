# adventure

A small text-adventure engine: a world of rooms in a JSON file and a state machine that runs player commands.

## Overview

- Python 3, standard library only.
- Validate a world with `python3 -m adventure check FILE`.

## Layout

- `adventure/world.py` loads and validates a world file.
- `adventure/state.py` holds the player's state.
- `adventure/engine.py` runs one command and returns the message.
- `worlds/` holds example world files.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m adventure check worlds/cave.json`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
