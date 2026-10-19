# rota

A command-line tool that builds a weekly staff rota from each person's available days.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m rota AVAILABILITY_FILE`.

## Layout

- `rota/availability.py` reads the availability file.
- `rota/planner.py` assigns people to days.
- `rota/__main__.py` prints the rota.
- `data/` holds example availability files.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m rota data/avail.txt`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
