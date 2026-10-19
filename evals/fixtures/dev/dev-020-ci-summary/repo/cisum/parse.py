"""Reading result files: one JSON object per job."""
import json
import os

STATUSES = ("passed", "failed", "flaky")


def load_results(directory):
    """Return a list of result dicts, sorted by job name."""
    results = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            result = json.load(handle)
        if result.get("status") not in STATUSES:
            raise ValueError(f"job {result.get('job')}: status must be passed, failed or flaky (got {result.get('status')!r})")
        results.append(result)
    return results
