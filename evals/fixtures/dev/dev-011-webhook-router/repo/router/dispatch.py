"""From a request body to a status code and payload."""
import time

from router.dedupe import SeenIds
from router.events import parse_event

MAX_AGE = 300
RETRY_AFTER = 30
_seen = SeenIds()


def response_headers(status):
    """Return the extra HTTP headers for a status code; 5xx asks the sender to wait."""
    if 500 <= status <= 599:
        return {"Retry-After": str(RETRY_AFTER)}
    return {}


def dispatch(body, registry, now=None, seen=None):
    """Return (status, payload) for one request body; repeated event ids are skipped."""
    now = time.time() if now is None else now
    seen = _seen if seen is None else seen
    try:
        event = parse_event(body)
    except ValueError as err:
        return 400, {"error": str(err)}
    if now - event["sent"] > MAX_AGE:
        return 400, {"error": "event is stale: timestamps older than 300 seconds are rejected"}
    handler = registry.get(event["type"])
    if handler is None:
        return 202, {"status": "ignored"}
    if not seen.claim(event["id"]):
        return 200, {"status": "duplicate"}
    try:
        handler(event)
    except Exception:
        seen.release(event["id"])
        raise
    return 200, {"status": "ok"}
