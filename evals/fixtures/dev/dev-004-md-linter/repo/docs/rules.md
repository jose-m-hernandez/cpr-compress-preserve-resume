# Rules

## no-tabs

Flags tab characters. Bad example:

```
	indented with a tab
```

## final-newline

Flags files without a final newline.

## line-length

Flags lines longer than 88 characters (not counting the line ending).

## trailing-space

Flags lines that end in spaces or tabs (not counting the line ending).

## heading-increment

Warning. Flags an ATX heading that skips a level, such as an h1 followed by an h3.
Going back up (h3 to h1) is fine, and `#` lines inside code fences are ignored.
Warnings print as `path:line: rule: warning: message` and do not make the exit code 1.

## no-bare-urls

Flags `http://` and `https://` URLs that are not inside a Markdown link. Inline links
`[text](url)`, `<url>` autolinks, `[text][ref]` links, reference definitions, code spans
and fenced code blocks are fine. Bad example:

```
See https://example.com for details.
```

## Output format

`--format text` (the default) prints `path:line: rule: message`. `--format json` prints
one JSON object per finding, one per line, with the keys `path`, `line`, `rule` and
`severity` (`error` or `warning`). Exit codes are the same in both formats.

## Config file

`--config PATH` reads a JSON file, conventionally named `.mdcheck.json`, that picks
which rules run:

```
{"rules": ["no-tabs", "line-length"]}
```

Without a config, all rules run. `--rules` on the command line overrides the config.
A missing file, invalid JSON, a wrong shape, or an unknown rule name exits with code 4.
