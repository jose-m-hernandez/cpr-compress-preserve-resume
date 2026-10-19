# renamer

Renames photo files using a text sidecar that lists a date and a title for each file.

## Overview

- Python 3, standard library only.
- Preview with `python3 -m renamer plan DIR`; DIR must contain an `index.txt` sidecar.

## Layout

- `renamer/sidecar.py` reads the sidecar into records.
- `renamer/plan.py` turns records into old and new names.
- `renamer/cli.py` parses arguments and prints the plan.
- `samples/` holds small example folders.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m renamer plan samples/basic`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
