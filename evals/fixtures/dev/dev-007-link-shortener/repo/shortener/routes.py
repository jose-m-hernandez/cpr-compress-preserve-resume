"""Request handling, independent of any server."""


def _shorten(body, store):
    """Store the URL in the body and answer 201 with its code."""
    try:
        code = store.add(body.strip())
    except ValueError as err:
        return 400, {}, str(err)
    return 201, {}, code


def _redirect(code, store):
    """Answer 302 to the URL stored under code, or 404."""
    url = store.get(code)
    if url is None:
        return 404, {}, "not found"
    return 302, {"Location": url}, ""


def handle(method, path, body, store):
    """Return a (status, headers, body) tuple for a request."""
    if path == "/shorten":
        if method == "POST":
            return _shorten(body, store)
        return 405, {"Allow": "POST"}, "method not allowed"
    if method == "GET" and path.startswith("/") and len(path) > 1:
        return _redirect(path[1:], store)
    return 404, {}, "not found"
