"""Converting a value between two units."""
from units.aliases import resolve
from units.table import FACTORS, TEMPERATURE


def convert(value, src, dst):
    """Convert value from unit src to unit dst, rounded to 6 significant digits."""
    src, dst = resolve(src), resolve(dst)
    if src in TEMPERATURE or dst in TEMPERATURE:
        raise ValueError("temperature needs an offset, not a factor, so it is not in the table")
    for unit in (src, dst):
        if unit not in FACTORS:
            raise ValueError(f"unknown unit {unit!r}")
    src_dim, src_factor = FACTORS[src]
    dst_dim, dst_factor = FACTORS[dst]
    if src_dim != dst_dim:
        raise ValueError(f"cannot convert {src_dim} to {dst_dim}")
    return float(f"{value * src_factor / dst_factor:.6g}")
