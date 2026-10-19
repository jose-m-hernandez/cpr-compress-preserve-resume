"""Removing old snapshots."""
import os
import re
import shutil

STAMP_PATTERN = re.compile(r"[0-9]{8}T[0-9]{6}")
DEFAULT_KEEP = 10


def is_snapshot_name(name):
    """Return True if name looks like a snapshot timestamp such as 20260502T101500."""
    return STAMP_PATTERN.fullmatch(name) is not None


def list_snapshots(dest_root):
    """Return the snapshot folder names, oldest first by name; other entries are ignored."""
    return sorted(
        name
        for name in os.listdir(dest_root)
        if is_snapshot_name(name) and os.path.isdir(os.path.join(dest_root, name))
    )


def prune(dest_root, keep=DEFAULT_KEEP):
    """Delete all but the newest `keep` snapshots and return the removed names."""
    names = list_snapshots(dest_root)
    doomed = names[:-keep] if keep else names
    for name in doomed:
        shutil.rmtree(os.path.join(dest_root, name))
    return doomed
