# notes-api

A small HTTP service that stores short notes in a JSON file.

## Overview

- Python 3, standard library only.
- Start the server with `python3 -m notes_api.app`.
- Responses are JSON.

## Layout

- `notes_api/app.py` is the HTTP layer.
- `notes_api/store.py` keeps notes in memory and saves them to a file.
- `config.json` holds runtime settings.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- List notes: `curl http://127.0.0.1:<port>/v1/notes` once the server is running.

## Conventions

- Four-space indentation.
- Keep handlers thin and put logic in the store.
- Every public function has a test.
- No third-party dependencies.
