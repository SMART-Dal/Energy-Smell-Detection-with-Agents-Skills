"""Cases for missing_early_exit."""

import re


def contains_target(rows, target):
    # Sets one constant and keeps scanning; nothing later can unset it.
    found = False
    for row in rows:
        if row.id == target:
            found = True
    return found


def all_records_valid(records):
    # A validation loop that learns the answer early and checks everything anyway.
    valid = True
    for record in records:
        if not record.check():
            valid = False
    return valid


def get_system_status(servers, limit):
    # A later iteration can overwrite it with a *different* value, so a `break`
    # would change the answer.
    status = "ALL_SYSTEMS_GO"
    for server in servers:
        if server.ping > limit:
            status = "SYSTEM_DEGRADED"
        elif server.offline:
            status = "SYSTEM_DOWN"
    return status


def seen_both_kinds(events):
    # Two independent flags: stopping at the first would miss the second.
    seen_start = False
    seen_end = False
    for event in events:
        if event.kind == "start":
            seen_start = True
        if event.kind == "end":
            seen_end = True
    return seen_start and seen_end


def first_match(rows, target):
    # Already exits.
    for row in rows:
        if row.id == target:
            return row
    return None


def stops_on_failure(records):
    # Already breaks.
    valid = True
    for record in records:
        if not record.check():
            valid = False
            break
    return valid


def collect_flags(rows):
    # The `if` body does real work, not a conclusive constant assignment.
    out = []
    for row in rows:
        if row.enabled:
            out.append(re.escape(row.name))
    return out
