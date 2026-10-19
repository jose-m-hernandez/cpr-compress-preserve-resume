"""Exception types and exit codes."""

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_CONFIG = 4


class UnknownRule(Exception):
    pass


class ConfigError(Exception):
    pass
