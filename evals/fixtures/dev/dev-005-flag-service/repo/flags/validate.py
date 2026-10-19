"""Flag name checks."""
import re

NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def check_name(name):
    if not NAME.match(name):
        raise ValueError("flag name must match ^[a-z][a-z0-9-]*$ (lowercase kebab-case)")
