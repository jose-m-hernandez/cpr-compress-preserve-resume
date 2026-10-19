# snap

A command-line tool that copies a directory into dated snapshots and prunes old ones.

## Overview

- Python 3, standard library only.
- Run it with `python3 -m snap snapshot SRC DEST` or `python3 -m snap prune DEST --keep N`.

## Layout

- `snap/snapshot.py` copies a directory into a new snapshot folder.
- `snap/prune.py` removes the oldest snapshots.
- `snap/cli.py` parses arguments and runs the commands.
- `samples/` holds a small example tree.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m snap snapshot samples/tree out`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
