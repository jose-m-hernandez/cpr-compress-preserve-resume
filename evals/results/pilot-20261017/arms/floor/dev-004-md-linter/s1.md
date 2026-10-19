# mdcheck

A small command-line linter for Markdown files.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m mdcheck FILE [FILE ...]`.
- Findings print as `path:line: rule: message`.

## Layout

- `mdcheck/rules.py` holds the lint rules.
- `mdcheck/runner.py` applies the rules to files.
- `mdcheck/cli.py` parses arguments and prints findings.
- `mdcheck/errors.py` holds exception types and exit codes.
- `samples/` holds example Markdown files.
- `docs/rules.md` documents each rule.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Lint a sample: `python3 -m mdcheck samples/good.md`.

## Conventions

- Four-space indentation and type hints on public functions.
- One function per rule, with a test for each.
- No third-party dependencies.
- Exit code 0 means clean and 1 means findings.
