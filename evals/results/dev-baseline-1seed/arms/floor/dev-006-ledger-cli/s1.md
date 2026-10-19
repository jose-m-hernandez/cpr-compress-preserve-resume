# ledger

A small command-line tool that summarises a plain-text expense ledger.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m ledger FILE`.
- It prints one line per category with the total spent.

## Layout

- `ledger/parse.py` turns ledger lines into entries.
- `ledger/summary.py` totals the entries and formats the report.
- `ledger/cli.py` parses arguments and prints the result.
- `data/` holds small example ledger files.
- `tests/` holds the unit tests.

## Ledger format

- One entry per line: `DATE | DESCRIPTION | AMOUNT | CATEGORY`.
- Blank lines and lines starting with `#` are ignored.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m ledger data/sample.txt`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- Errors are reported as `error: line N: ...` on standard error.
