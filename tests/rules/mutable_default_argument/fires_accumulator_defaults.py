"""Literal mutable defaults that the body then appends to.

This is the textbook shape: the list and the dict are built once, when the
`def` executes, so the second call sees whatever the first call left behind.
Both a positional default and a keyword-only default are covered here, because
they live in different fields of `ast.arguments` and a rule that only reads
`defaults` would miss the second one.
"""

from __future__ import annotations


def collect_warnings(message, into=[]):  # EXPECT
    """Append one warning and hand back the whole batch so far."""
    into.append(message)
    return into


def tag_record(record, *, labels={}):  # EXPECT
    """Attach a label set to a record, remembering labels between calls."""
    labels[record.id] = record.name
    return labels


def register_hosts(name, address, seen=set()):  # EXPECT
    """Keep the hosts we have already registered, to skip duplicates."""
    if name in seen:
        return False
    seen.add(name)
    return address is not None
