"""Print the summary for a results folder."""
import sys

from cisum.parse import load_results
from cisum.summary import summarise


def main(argv):
    if len(argv) != 1:
        print("usage: python3 -m cisum RESULTS_DIR", file=sys.stderr)
        return 2
    try:
        results = load_results(argv[0])
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    summary = summarise(results)
    print(f"passed: {summary['passed']}  failed: {summary['failed']}  flaky: {summary['flaky']}")
    print(f"total seconds: {summary['seconds']}")
    if summary["slow"]:
        print("slow jobs:")
        for result in summary["slow"]:
            print(f"  {result.get('job')}: {result['seconds']}s")
    return 1 if summary["failed"] else 0


raise SystemExit(main(sys.argv[1:]))
