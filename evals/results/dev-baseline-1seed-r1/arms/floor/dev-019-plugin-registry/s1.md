# plugins

A small library for registering plugins by name and looking them up later.

## Overview

- Python 3, standard library only.
- Check a list of plugin names with `python3 -m plugins check FILE`.

## Layout

- `plugins/registry.py` holds the registry.
- `plugins/__main__.py` is the command-line entry point.
- `data/` holds example name lists.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m plugins check data/names.txt`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
