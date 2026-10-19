# router

A small webhook router: it validates incoming events and passes each one to the handler for its type.

## Overview

- Python 3, standard library only.
- Replay a saved event with `python3 -m router replay FILE`.

## Layout

- `router/events.py` parses and checks an incoming event.
- `router/registry.py` maps event types to handlers.
- `router/dispatch.py` turns a request body into a status code and a payload.
- `data/` holds saved example events.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Try it: `python3 -m router replay data/ping.json`.

## Conventions

- Four-space indentation and docstrings on public functions.
- Keep functions short and give each one a test.
- No third-party dependencies.
