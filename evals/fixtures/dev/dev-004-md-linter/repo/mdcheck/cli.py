"""Command-line interface."""
import argparse
import sys

from mdcheck.errors import EXIT_CLEAN, EXIT_CONFIG, EXIT_FINDINGS, ConfigError, UnknownRule
from mdcheck.formats import FORMATS, format_finding, severity
from mdcheck.runner import check_files, load_config


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mdcheck", description="Lint Markdown files.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--rules", help="comma-separated rule names to run")
    parser.add_argument("--config", help="JSON file (e.g. .mdcheck.json) listing the rules to run")
    parser.add_argument("--format", choices=FORMATS, default="text", help="output format")
    args = parser.parse_args(argv)
    names = args.rules.split(",") if args.rules else None
    try:
        if names is None and args.config:
            names = load_config(args.config)
        findings = check_files(args.paths, names)
    except (ConfigError, UnknownRule) as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_CONFIG
    errors = 0
    for path, number, rule, message in findings:
        if severity(rule) == "error":
            errors += 1
        print(format_finding(args.format, path, number, rule, message))
    return EXIT_FINDINGS if errors else EXIT_CLEAN
