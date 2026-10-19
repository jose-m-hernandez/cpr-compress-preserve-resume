# shortener

A tiny link shortener that keeps its links in memory.

## Overview

- Python 3, standard library only.
- Run the URL check with `python3 -m shortener check URL`.

## Layout

- `shortener/store.py` holds the in-memory store.
- `shortener/urls.py` checks a URL before it is stored.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Check a URL: `python3 -m shortener check https://example.com/a`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
