"""Counting outcomes."""


SLOW_SECONDS = 120


def slow_jobs(results):
    """Return the results of jobs that took more than SLOW_SECONDS."""
    return [r for r in results if r.get("seconds", 0) > SLOW_SECONDS]


def unique_jobs(results):
    """Merge results whose job names differ only in case; the last one wins."""
    merged = {}
    for index, result in enumerate(results):
        name = result.get("job")
        key = name.lower() if isinstance(name, str) else ("unnamed", index)
        merged.pop(key, None)
        merged[key] = result
    return list(merged.values())


def summarise(results):
    """Return counts per status, the total seconds and the slow jobs."""
    results = unique_jobs(results)
    summary = {"passed": 0, "failed": 0, "flaky": 0, "seconds": 0}
    for result in results:
        summary[result["status"]] += 1
        summary["seconds"] += result.get("seconds", 0)
    summary["slow"] = slow_jobs(results)
    return summary
