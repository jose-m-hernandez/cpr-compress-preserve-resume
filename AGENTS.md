# AGENTS.md

This file provides guidance to Claude Code, Codex and other agents when working with code in this repository.

## Project Overview

This is a fork of `cpr-compress-preserve-resume` (upstream: not this org). It
ships three Claude Code skills — `/preserve`, `/compress`, `/resume` — as
`.md` command files in `commands/`, plus `scripts/dump_transcript.py`, which
gives Claude Code persistent memory across sessions by writing to CLAUDE.md
and session logs.

## Build, Test, Run

There is no build step or package manifest. Install by copying files:

```bash
mkdir -p ~/.claude/commands ~/.claude/scripts
cp commands/*.md ~/.claude/commands/
cp scripts/dump_transcript.py ~/.claude/scripts/
```

`dump_transcript.py` requires Python 3.10+. There is no automated test
suite; the README's manual smoke test is running `/compress` inside Claude
Code and confirming the preservation prompt appears.

## Conventions

- This is a fork; treat upstream-authored files as given and keep changes
  minimal and factual until a divergence is deliberate.

See README.md for the full skill descriptions, installation options, and
usage examples.
