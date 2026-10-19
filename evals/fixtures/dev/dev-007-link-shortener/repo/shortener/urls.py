"""URL checks."""


def check_url(url):
    """Return the URL unchanged, or raise ValueError if it cannot be shortened."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http and https urls can be shortened")
    return url
