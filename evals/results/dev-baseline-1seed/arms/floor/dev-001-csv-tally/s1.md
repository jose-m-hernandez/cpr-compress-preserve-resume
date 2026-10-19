# tally

A small command-line tool that sums and counts columns in CSV files.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m tally FILE --column NAME`.
- It prints one number to standard output.

## Layout

- `tally/core.py` reads rows and sums a column.
- `tally/cli.py` parses arguments and prints the result.
- `tests/` holds the unit tests.
- `samples/` holds small example input files.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m tally samples/basic.csv --column amount`.

## Conventions

- Four-space indentation and type hints on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
- Error messages name the column and the row number.
