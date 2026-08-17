"""The repair itself: `None` as the default, the object built in the body.

This is what the rule's suggested fix produces, so it must stay quiet -- a rule
that still fired after its own repair had been applied would be unusable.  The
walrus and the `or` spelling are included because both turn up in real code and
neither puts a mutable node anywhere near the signature.
"""

from __future__ import annotations


def collect_warnings(message, into=None):
    """Append one warning to a batch the caller owns."""
    if into is None:
        into = []
    into.append(message)
    return into


def group_by_owner(records, buckets=None):
    """Group records under their owner, starting a fresh mapping per call."""
    buckets = buckets if buckets is not None else {}
    for record in records:
        buckets.setdefault(record.owner, []).append(record)
    return buckets


def merge_settings(overrides, base=None):
    """Layer overrides on top of a base mapping."""
    merged = dict(base or {})
    merged.update(overrides)
    return merged
