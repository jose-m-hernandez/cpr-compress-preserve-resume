"""The footer added to every message."""

FOOTER = "Use the link to unsubscribe"


def add_footer(text):
    """Return the text with the footer on its own line after a blank line."""
    return text.rstrip("\n") + "\n\n" + FOOTER + "\n"
