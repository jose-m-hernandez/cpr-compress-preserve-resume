# flag-service

A small HTTP service that answers whether a feature flag is on.

## Overview

- Python 3, standard library only.
- Start the server with `python3 -m flags.app`.
- `GET /flags/<name>` answers with JSON such as `{"enabled": true}`.

## Layout

- `flags/app.py` is the HTTP layer.
- `flags/store.py` defines and evaluates flags.
- `flags/validate.py` checks flag names.
- `flags/cache.py` caches evaluations for a short time.
- `config/flags.json` holds the flag definitions.
- `tests/` holds the unit tests.

## Commands

- Run the tests: `python3 -m unittest discover tests`.
- Query a flag: `curl http://127.0.0.1:8090/flags/dark-mode` once the server is running.

## Conventions

- Four-space indentation.
- Keep the HTTP layer thin and put logic in the store.
- Every public function has a test.
- No third-party dependencies.
