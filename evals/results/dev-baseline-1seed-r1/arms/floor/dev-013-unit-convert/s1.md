# units

A small library that converts between units of length and mass.

## Overview

- Python 3, standard library only.
- Convert from the command line with `python3 -m units VALUE FROM TO`.

## Layout

- `units/table.py` holds the conversion factors.
- `units/convert.py` does the conversion.
- `units/__main__.py` is the command-line entry point.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m units 5 km mi`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
