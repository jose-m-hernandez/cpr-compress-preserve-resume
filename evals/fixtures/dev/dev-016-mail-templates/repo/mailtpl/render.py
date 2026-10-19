"""Filling in a template."""
import re

from mailtpl.footer import add_footer

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def placeholders(text):
    """Return the placeholder names used in a template."""
    return PLACEHOLDER.findall(text)


class MissingValue(ValueError):
    """A placeholder has no value, or only a blank one."""


def _value_for(name, values):
    """Return the text for a placeholder or raise MissingValue."""
    value = values.get(name)
    if value is None or not str(value).strip():
        raise MissingValue(f"no value for placeholder {name!r}")
    return str(value)


def render(text, values):
    """Replace each {name} with its value and append the footer.

    Raise MissingValue if a placeholder has no value.
    """
    body = PLACEHOLDER.sub(lambda m: _value_for(m.group(1), values), text)
    return add_footer(body)
