"""Rendering the summary as markdown."""


def render_markdown(summary):
    """Return the summary as a markdown table, with slow jobs listed below."""
    lines = [
        "| Passed | Failed | Flaky | Total seconds |",
        "| ---: | ---: | ---: | ---: |",
        f"| {summary['passed']} | {summary['failed']} | {summary['flaky']} | {summary['seconds']} |",
    ]
    if summary["slow"]:
        lines += ["", "| Slow job | Seconds |", "| --- | ---: |"]
        for result in summary["slow"]:
            lines.append(f"| {result.get('job')} | {result['seconds']} |")
    return "\n".join(lines) + "\n"
