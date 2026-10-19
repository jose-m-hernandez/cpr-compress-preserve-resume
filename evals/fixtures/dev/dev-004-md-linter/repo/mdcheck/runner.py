"""Applying rules to files."""
import json

from mdcheck.errors import ConfigError, UnknownRule
from mdcheck.rules import RULES


def load_config(path: str) -> list:
    """Read the rule names from a JSON config like {"rules": ["no-tabs"]}."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as error:
        raise ConfigError(f"cannot read config {path!r}: {error.strerror}") from error
    except ValueError as error:
        raise ConfigError(f"invalid JSON in config {path!r}: {error}") from error
    names = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ConfigError(f'config {path!r} must look like {{"rules": ["no-tabs"]}}')
    return names


def select_rules(names=None):
    known = dict(RULES)
    if not names:
        return list(RULES)
    chosen = []
    for name in names:
        if name not in known:
            raise UnknownRule(f"unknown rule {name!r}; known rules: {', '.join(sorted(known))}")
        chosen.append((name, known[name]))
    return chosen


def check_files(paths, names=None):
    findings = []
    rules = select_rules(names)
    for path in paths:
        with open(path, encoding="utf-8", newline="") as handle:
            lines = handle.readlines()
        for rule_name, rule in rules:
            for number, message in rule(lines):
                findings.append((path, number, rule_name, message))
    return findings
