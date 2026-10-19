"""Output formatting for findings."""
import json

from mdcheck.rules import WARNING_RULES

FORMATS = ["text", "json"]


def severity(rule: str) -> str:
    return "warning" if rule in WARNING_RULES else "error"


def format_finding(fmt: str, path: str, number: int, rule: str, message: str) -> str:
    level = severity(rule)
    if fmt == "json":
        return json.dumps({"path": path, "line": number, "rule": rule, "severity": level})
    if level == "warning":
        return f"{path}:{number}: {rule}: warning: {message}"
    return f"{path}:{number}: {rule}: {message}"
