# inventory

Compares two JSON stock lists and reports what changed between them.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m inventory OLD.json NEW.json`.

## Layout

- `inventory/loader.py` reads and validates a stock list.
- `inventory/diff.py` compares two stock lists.
- `inventory/cli.py` parses arguments and prints a table.
- `data/` holds small example stock lists.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m inventory data/old.json data/new.json`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
