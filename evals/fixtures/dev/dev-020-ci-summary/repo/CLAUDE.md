# cisum

A script that summarises a folder of CI job result files.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m cisum RESULTS_DIR`.

## Layout

- `cisum/parse.py` reads the result files.
- `cisum/summary.py` counts outcomes and adds up time.
- `cisum/__main__.py` prints the summary.
- `samples/` holds example result folders.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m cisum samples/run1`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
