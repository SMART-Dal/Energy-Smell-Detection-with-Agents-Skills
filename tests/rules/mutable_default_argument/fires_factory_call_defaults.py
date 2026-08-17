"""Mutable defaults written as constructor calls rather than literals.

`Counter()`, `defaultdict(list)` and `bytearray()` look less like a literal, so
they read as if they were evaluated per call.  They are not: the call runs once
at definition time and every caller shares the object.  This is a different
shape from the literal case, and a rule that only matched `ast.List` and
friends would let all three through.
"""

from __future__ import annotations

from collections import Counter, defaultdict


def tally_events(event, counts=Counter()):  # EXPECT
    """Count events by type across the process."""
    counts[event.type] += 1
    return counts


def group_by_owner(
    record,
    buckets=defaultdict(list),  # EXPECT
):
    """Group records under their owner."""
    buckets[record.owner].append(record)
    return buckets


def accumulate_frame(chunk, sink=bytearray()):  # EXPECT
    """Append one chunk to the frame being assembled."""
    sink.extend(chunk)
    return sink
