"""Lint rules. A rule takes the list of lines and returns (line_number, message) pairs."""
import re


def final_newline(lines):
    if lines and not lines[-1].endswith("\n"):
        return [(len(lines), "file does not end with a newline")]
    return []


def no_tabs(lines):
    return [(number, "tab character") for number, line in enumerate(lines, start=1) if "\t" in line]


MAX_LINE_LENGTH = 88


def line_length(lines):
    return [
        (number, f"line longer than {MAX_LINE_LENGTH} characters")
        for number, line in enumerate(lines, start=1)
        if len(line.rstrip("\r\n")) > MAX_LINE_LENGTH
    ]


def trailing_space(lines):
    return [
        (number, "trailing whitespace")
        for number, line in enumerate(lines, start=1)
        if line.rstrip("\r\n").endswith((" ", "\t"))
    ]


HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]|$)")
FENCE = re.compile(r"^ {0,3}(```|~~~)")


def heading_increment(lines):
    findings = []
    previous = None
    fence = None
    for number, line in enumerate(lines, start=1):
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif fence == marker.group(1):
                fence = None
            continue
        match = None if fence else HEADING.match(line)
        if not match:
            continue
        level = len(match.group(1))
        if previous is not None and level > previous + 1:
            findings.append((number, f"heading level jumps from h{previous} to h{level}"))
        previous = level
    return findings


URL = re.compile(r"https?://\S+")
# Spans where a URL is not bare: code spans, [text](url) links, <url> autolinks,
# and [text][ref] links.
NOT_BARE = re.compile(r"`[^`]*`|\[[^\]]*\]\([^)]*\)|<https?://[^>]*>|\[[^\]]*\]\[[^\]]*\]")
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:")


def no_bare_urls(lines):
    findings = []
    fence = None
    for number, line in enumerate(lines, start=1):
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif fence == marker.group(1):
                fence = None
            continue
        if fence or REFERENCE_DEFINITION.match(line):
            continue
        for match in URL.finditer(NOT_BARE.sub("", line)):
            findings.append((number, f"bare URL {match.group().rstrip('.,;:!?)')}; use a link"))
    return findings


RULES = [
    ("final-newline", final_newline),
    ("no-tabs", no_tabs),
    ("line-length", line_length),
    ("trailing-space", trailing_space),
    ("heading-increment", heading_increment),
    ("no-bare-urls", no_bare_urls),
]

# Rules whose findings are reported as warnings and do not make the exit code 1.
WARNING_RULES = {"heading-increment"}
