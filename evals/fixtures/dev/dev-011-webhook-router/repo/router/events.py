"""Parsing incoming events."""
import json


def normalise_legacy_kind(event):
    """Rename the legacy "kind" field to "type"; remove after the March cutover."""
    if "kind" in event:
        event = dict(event)
        legacy = event.pop("kind")
        event.setdefault("type", legacy)
    return event


def parse_event(body):
    """Return the event dict, or raise ValueError if the body is not a usable event."""
    try:
        event = json.loads(body)
    except ValueError:
        raise ValueError("body is not valid JSON")
    if not isinstance(event, dict):
        raise ValueError("body must be a JSON object")
    event = normalise_legacy_kind(event)
    for key in ("id", "type", "sent"):
        if key not in event:
            raise ValueError(f"event has no {key!r} field")
    return event
