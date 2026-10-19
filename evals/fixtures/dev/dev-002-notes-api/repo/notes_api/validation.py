"""Input checks for notes."""

MAX_TITLE = 80


def validate_title(title):
    if len(title) > MAX_TITLE:
        raise ValueError("title too long (max 80)")
