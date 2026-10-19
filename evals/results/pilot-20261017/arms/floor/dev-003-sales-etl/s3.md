# sales-etl

A small script that loads a sales CSV and reports revenue per product.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m etl data/sales_2025.csv`.
- Output is one tab-separated line per SKU.

## Layout

- `etl/load.py` reads the CSV into dictionaries.
- `etl/transform.py` computes revenue per SKU.
- `etl/__main__.py` is the command-line entry point.
- `data/` holds input files.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Run the report: `python3 -m etl data/sales_2025.csv`.

## Conventions

- Four-space indentation.
- Pure functions in `transform.py`; all file access stays in `load.py`.
- Every public function has a test.
- No third-party dependencies.
