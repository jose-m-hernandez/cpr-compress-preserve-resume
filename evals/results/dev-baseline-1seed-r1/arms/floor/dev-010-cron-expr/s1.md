# cronish

A small library that parses cron-like schedule expressions.

## Overview

- Python 3, standard library only.
- Inspect an expression with `python3 -m cronish 'MINUTE HOUR WEEKDAY'`.

## Layout

- `cronish/parser.py` parses an expression into a schedule.
- `cronish/__main__.py` prints the parsed fields.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m cronish '*/15 9-17 1-5'`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
