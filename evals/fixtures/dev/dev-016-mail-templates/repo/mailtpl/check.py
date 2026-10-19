"""Checking a template."""
from mailtpl.render import placeholders

ALLOWED = ("name", "plan", "link")
MAX_SUBJECT = 60


def check_subject_length(text):
    """Raise ValueError if the subject is longer than MAX_SUBJECT characters."""
    first_line = text.split("\n", 1)[0]
    subject = first_line[len("Subject:"):].strip()
    if len(subject) > MAX_SUBJECT:
        raise ValueError(
            f"subject is {len(subject)} characters; the limit is {MAX_SUBJECT} "
            "because phones cut longer ones off"
        )


def check_template(text):
    """Raise ValueError for the first problem found."""
    if not text.startswith("Subject:"):
        raise ValueError("the first line must start with 'Subject:'")
    check_subject_length(text)
    for name in placeholders(text):
        if name not in ALLOWED:
            raise ValueError(f"unknown placeholder {name!r}; allowed placeholders are name, plan and link")
