"""Reusable assertions and measurement helpers."""
import time
from contextlib import contextmanager


def assert_in_range(name, value, low, high):
    if not (low <= value <= high):
        raise AssertionError(f"{name}={value} outside allowed range [{low}, {high}]")


@contextmanager
def timed():
    """Measure wall time of a block: `with timed() as t: ...; t['s']`."""
    box = {}
    start = time.perf_counter()
    try:
        yield box
    finally:
        box["s"] = time.perf_counter() - start


def percentile(data, pct):
    ordered = sorted(data)
    idx = min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))
    return ordered[idx]
