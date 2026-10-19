"""Making a snapshot."""
import datetime
import os
import shutil

from snap.manifest import write_manifest


def make_stamp(now=None):
    """Return a UTC timestamp like 20260502T101500, which sorts chronologically."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")


def check_destination(src, dest_root):
    """Refuse a destination that sits inside the source tree."""
    src_real = os.path.realpath(src)
    dest_real = os.path.realpath(dest_root)
    if dest_real == src_real or dest_real.startswith(src_real + os.sep):
        raise ValueError("destination is inside the source; a snapshot would copy itself")


def snapshot(src, dest_root, stamp):
    """Copy src into dest_root/stamp and return the new folder."""
    check_destination(src, dest_root)
    target = os.path.join(dest_root, stamp)
    shutil.copytree(src, target)
    write_manifest(target)
    return target
