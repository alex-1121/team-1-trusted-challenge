"""What a generalised released value can stand for.

The repair writes coarser values on the rows it touches: a wider age band ("20-39"), an explicit hour block
("03:00 to 05:59"), a place set to "other", a coarser grid, a shorter postcode, a month instead of a date, or
"suppressed". An attacker cannot rule such a row out for any original value it covers, so every attack and check
that matches facts against the release asks `covers`, never plain equality.
"""
import re

SUPPRESSED = "suppressed"
BLOCK = re.compile(r"^(\d\d):00 to (\d\d):59$")
HOUR = re.compile(r"^(\d\d):00$")
BAND = re.compile(r"^(\d+)-(\d+)$")


def hour_block(start, block):
    """The repair's hour block, written so nobody (and no parser) mistakes it for an exact hour."""
    start = start - start % block
    return f"{start:02d}:00 to {min(start + block - 1, 23):02d}:59"


def hours(v):
    """Hours of the day a released time value can stand for (all 24 when suppressed or missing)."""
    if not isinstance(v, str) or v == SUPPRESSED or v == "":
        return set(range(24))
    m = HOUR.match(v)
    if m:
        return {int(m.group(1))}
    m = BLOCK.match(v)
    if m:
        return set(range(int(m.group(1)), int(m.group(2)) + 1))
    return set(range(24))


def band_range(v):
    if not isinstance(v, str):
        return None
    if v.endswith("+") and v[:-1].isdigit():
        return int(v[:-1]), 200
    m = BAND.match(v)
    return (int(m.group(1)), int(m.group(2))) if m else None


def age_ok(v, age):
    """Can a released age value (band, number or suppressed) belong to someone of this age?"""
    if v == SUPPRESSED:
        return True
    r = band_range(v)
    if r:
        return r[0] <= age <= r[1]
    try:
        return int(float(v)) == age
    except (TypeError, ValueError):
        return False


def covers(rv, bv, ops=()):
    """Can released value rv stand for bv, the value at the release's base precision? ops: the repair ladder steps
    (dicts with "op") that may have touched this column."""
    if rv == bv or rv == SUPPRESSED:
        return True
    if not isinstance(rv, str) or not isinstance(bv, str):
        return False
    for step in ops:
        op = step["op"]
        if op == "set" and rv == step["value"]:
            return True
        if op == "widen_band":
            r, b = band_range(rv), band_range(bv)
            if r and b and r[0] <= b[0] <= r[1]:
                return True
        if op == "widen_hour" and HOUR.match(bv) and int(bv[:2]) in hours(rv):
            return True
        if op == "round":
            try:
                if round(float(bv), step["decimals"]) == float(rv):
                    return True
            except ValueError:
                pass
        if op == "prefix" and len(rv) < len(bv) and bv.startswith(rv):
            return True
        if op == "to_day" and len(rv) == 10 and bv[:10] == rv:
            return True
        if op == "to_month" and bv[:7] == rv:
            return True
    return False
