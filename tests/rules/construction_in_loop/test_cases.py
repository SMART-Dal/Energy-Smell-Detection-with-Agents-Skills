"""Cases for construction_in_loop."""

import re


def group_rows(rows):
    # A fresh empty-ish literal per iteration, thrown away each time.
    out = []
    for row in rows:
        bucket = {"id": row.id, "cells": []}
        out.append(bucket)
    return out


def select_allowed(values, limit):
    # A set literal rebuilt on every pass; it depends only on `limit`.
    kept = []
    for value in values:
        allowed = {i for i in range(1, limit, 2)}
        if value in allowed:
            kept.append(value)
    return kept


def sort_each_group(groups):
    # A lambda object is constructed per iteration.
    return [sorted(g, key=lambda item: item.rank) for g in groups]


def tally_by_kind(records):
    # `dict()` is a constructor call, not a literal, and costs the same.
    seen = []
    for record in records:
        counters = dict()
        counters[record.kind] = 1
        seen.append(counters)
    return seen


def reuse_one_buffer(rows):
    # Built once above the loop: this is the repair, not the smell.
    buffer = []
    for row in rows:
        buffer.clear()
        buffer.append(row.value)
    return len(buffer)


def collect_pairs(rows):
    # An empty literal costs almost nothing and is excluded on purpose.
    out = []
    for row in rows:
        parts = []
        parts.append(row.value)
        out.append(parts)
    return out


def constant_iterable(rows):
    # The loop's own iterable is evaluated once, not per iteration.
    total = 0
    for row in rows:
        for flag in ("a", "b"):
            total += row.get(flag, 0)
    return total


def compiled_once(lines, pattern):
    # Hoisted above the loop already.
    matcher = re.compile(pattern)
    return [matcher.search(line) for line in lines]
