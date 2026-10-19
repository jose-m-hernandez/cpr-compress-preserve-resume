"""Clean-room lint for the evals tree.

Scans every file under evals/ (minus any _raw/ directory) and every file under tests/
whose path contains "evals" for generic leak patterns (evals/cleanroom-public.txt) and for private terms
read from the files named in CPR_EVAL_PRIVATE_TERMS. File names are matched too.
Findings are reported as path:line: label and never quote the matched text.
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_VAR = "CPR_EVAL_PRIVATE_TERMS"
# The only two files exempt from the public rules: they hold the patterns and the canary.
EXEMPT = frozenset({"evals/cleanroom-public.txt", "tests/test_evals_cleanroom.py"})
SKIP_DIRS = frozenset({"__pycache__"})


class TermsError(Exception):
    pass


class ScanError(Exception):
    """A scan that cannot be completed. The message is a path-free label; the lint exits 3."""


_ZERO_WIDTH = dict.fromkeys([0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x0000])


def normalize(text: str) -> str:
    """NFKC, then drop zero-width characters and NUL; NBSP becomes a plain space (NFKC does that)."""
    return unicodedata.normalize("NFKC", text).replace("\u00a0", " ").translate(_ZERO_WIDTH)


def decode(data: bytes) -> str:
    """UTF-16 when a BOM says so, otherwise UTF-8 with replacement."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8", errors="replace")


def load_public(path: Path) -> list:
    rules = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        label, sep, pattern = raw.partition("\t")
        if not sep or not label.strip() or not pattern:
            raise ValueError(f"{path.name}:{number}: expected label<TAB>regex")
        rules.append((label.strip(), re.compile(pattern)))
    return rules


def load_terms(paths: list) -> list:
    """Return [(label, casefolded term)]. A missing or empty file raises TermsError."""
    terms = []
    for index, path in enumerate(paths, start=1):
        try:
            text = Path(path).expanduser().read_text(encoding="utf-8-sig")
        except OSError:
            raise TermsError(f"private terms file {index} is missing or unreadable")
        before = len(terms)
        for number, raw in enumerate(text.splitlines(), start=1):
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            terms.append((f"private-{index}:{number}", normalize(value).casefold()))
        if len(terms) == before:
            raise TermsError(f"private terms file {index} has no terms")
    return terms


def term_paths_from_env(env) -> list:
    value = env.get(ENV_VAR, "")
    return [Path(p) for p in value.split(os.pathsep) if p.strip()]


def _walk_error(exc: OSError):
    raise ScanError("directory unreadable")


REPLACEMENT_RATIO_MAX = 0.05


def _check_text(path: Path) -> None:
    """A file the lint reads must be text: NUL bytes or a high share of replacement characters when decoded as UTF-8
    make the scan unreliable, so the scan stops. UTF-16 with a BOM is text."""
    try:
        data = path.read_bytes()
    except OSError:
        raise ScanError("file unreadable")
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return
    if b"\x00" in data:
        raise ScanError("non-text file (NUL bytes)")
    text = data.decode("utf-8", errors="replace")
    if text and text.count("\ufffd") / len(text) > REPLACEMENT_RATIO_MAX:
        raise ScanError("non-text file (not UTF-8)")


def _walk(base: Path) -> list:
    """Every file under base, sorted. A symlinked directory or a non-text file raises ScanError (never skipped)."""
    found = []
    for dirpath, dirnames, filenames in os.walk(base, onerror=_walk_error):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        if any(os.path.islink(os.path.join(dirpath, d)) for d in dirnames):
            raise ScanError("symlinked directory")
        for name in sorted(filenames):
            path = Path(dirpath) / name
            _check_text(path)
            found.append(path)
    return found


def collect(root: Path) -> list:
    files = []
    evals = root / "evals"
    if evals.is_dir():
        files += [p for p in _walk(evals) if "_raw" not in p.relative_to(evals).parts[:-1]]
    tests = root / "tests"
    if tests.is_dir():
        files += [p for p in _walk(tests) if "evals" in p.relative_to(tests).as_posix().lower()]
    return files


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, rel: str, rules: list, terms: list) -> list:
    """Return sorted unique (line, label) findings; line 0 means the file name.

    rel is the name matched on line 0: the repo-relative path for repo scope, and
    only the components at or below the argument for a --path target. Text is
    normalized first; private terms are also matched against each line joined to
    the next, which catches a term split across a line break.
    """
    try:
        lines = [normalize(l) for l in decode(path.read_bytes()).splitlines()]
    except OSError:
        raise ScanError("file unreadable")
    hits = set()
    entries = [(0, normalize(rel))] + list(enumerate(lines, start=1))
    for index, (number, text) in enumerate(entries):
        here = text.casefold()
        nxt = entries[index + 1][1].casefold() if index + 1 < len(entries) and number > 0 else None
        for label, term in terms:
            if term in here:
                hits.add((number, label))
            elif nxt is not None and term not in nxt and (term in here + nxt or term in here + " " + nxt):
                hits.add((number, label))  # split across the line break
        for label, regex in rules:
            if regex.search(text):
                hits.add((number, label))
    return sorted(hits)


def scan(root: Path, extra: list, rules: list, terms: list) -> tuple:
    """Return (findings as [(rel, line, label)], file count)."""
    findings = []
    targets = [(p, _rel(p, root), _rel(p, root), _rel(p, root) in EXEMPT) for p in collect(root)]
    for extra_path in extra:
        extra_path = Path(extra_path)
        if not extra_path.exists():
            raise ScanError("path missing or dangling")
        if extra_path.is_dir():
            targets += [(p, _rel(p, root), p.relative_to(extra_path).as_posix(), False) for p in _walk(extra_path)]
        else:
            targets.append((extra_path, _rel(extra_path, root), extra_path.name, False))
    for path, display, match_name, exempt in targets:
        active = [] if exempt else rules
        for line, label in scan_file(path, match_name, active, terms):
            findings.append((display, line, label))
    return findings, len(targets)


def _mask(text: str, terms: list) -> str:
    """Replace every private term in a printed path with ***, so names never leak it."""
    for _, term in terms:
        text = re.sub(re.escape(term), "***", text, flags=re.IGNORECASE)
    return text


def run_lint(root: Path, extra: list, env, out=None) -> int:
    out = out or sys.stdout
    term_paths = term_paths_from_env(env)
    if not term_paths:
        print("cleanroom: private terms not configured", file=out)
        return 3
    try:
        terms = load_terms(term_paths)
        rules = load_public(root / "evals" / "cleanroom-public.txt")
    except (TermsError, ValueError, OSError) as exc:
        print(f"cleanroom: {exc}", file=out)
        return 3
    try:
        findings, _ = scan(root, extra, rules, terms)
    except ScanError as exc:
        print(f"cleanroom: scan incomplete: {exc}", file=out)
        return 3
    for rel, line, label in findings:
        print(f"{_mask(rel, terms)}:{line}: {label}", file=out)
    print(
        f"cleanroom: {len(findings)} findings (public rules {len(rules)}, "
        f"private terms {len(terms)} from {len(term_paths)} files)",
        file=out,
    )
    return 0 if not findings else 1
