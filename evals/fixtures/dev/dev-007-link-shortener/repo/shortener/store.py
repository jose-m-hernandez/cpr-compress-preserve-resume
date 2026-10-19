"""The in-memory link store."""
import string
import time

from shortener.urls import check_url

ALPHABET = string.digits + string.ascii_lowercase
CODE_LENGTH = 6
TTL_SECONDS = 7 * 24 * 60 * 60


def encode(number):
    """Return number as a zero-padded base 36 code of CODE_LENGTH characters."""
    if not 0 <= number < len(ALPHABET) ** CODE_LENGTH:
        raise ValueError("out of short codes")
    digits = []
    for _ in range(CODE_LENGTH):
        number, digit = divmod(number, len(ALPHABET))
        digits.append(ALPHABET[digit])
    return "".join(reversed(digits))


class Store:
    """Maps short codes to URLs that expire after 7 days."""

    def __init__(self, clock=time.time):
        self._clock = clock
        self._urls = {}
        self._next = 0

    def add(self, url):
        """Store a URL and return its short code, counting up from 000000."""
        check_url(url)
        code = encode(self._next)
        self._next += 1
        self._urls[code] = (url, self._clock() + TTL_SECONDS)
        return code

    def get(self, code):
        """Return the URL for a code, or None if unknown or expired."""
        entry = self._urls.get(code)
        if entry is None:
            return None
        url, expires = entry
        if self._clock() >= expires:
            del self._urls[code]
            return None
        return url
