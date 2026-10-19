"""Command-line interface."""
import argparse
import sys

from snap.prune import DEFAULT_KEEP, prune
from snap.snapshot import make_stamp, snapshot


def build_parser():
    parser = argparse.ArgumentParser(prog="snap")
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("src")
    snap.add_argument("dest")
    pr = sub.add_parser("prune")
    pr.add_argument("dest")
    pr.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    return parser


def main(argv):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            print(snapshot(args.src, args.dest, make_stamp()))
        else:
            for name in prune(args.dest, args.keep):
                print("removed", name)
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0
