# metrics

A tiny metrics endpoint: counters held in memory and served as plain text.

## Overview

- Python 3, standard library only.
- Check a list of metric names with `python3 -m metrics check FILE`.

## Layout

- `metrics/registry.py` holds counters in a registry.
- `metrics/check.py` checks metric names.
- `metrics/__main__.py` is the command-line entry point.
- `data/` holds example name lists.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m metrics check data/names.txt`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
