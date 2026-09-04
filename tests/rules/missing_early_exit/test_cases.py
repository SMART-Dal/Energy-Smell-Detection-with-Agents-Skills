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


def collect_problems(records):
    # Appends on a match rather than setting a flag: this is a fold, and a
    # `break` would report the first bad row instead of all of them.
    problems = []
    for position, record in enumerate(records):
        if record % 97 == 0:
            problems.append(position)
    return problems


def audit_every_row(stream, stats):
    # The loop is doing work for somebody else: a call out to a function this
    # unit cannot see, and a counter on an object the caller is holding.
    # Breaking early stops both.
    found = False
    for item in stream:
        log_event(item)
        stats.total += 1
        if item.is_target:
            found = True
    return found


def reset_each_pass(items):
    # Re-initialised at the top of every pass and consumed at the bottom, so
    # the loop is not settling anything -- `valid` means "this item".
    for item in items:
        valid = False
        if item.passes_check:
            valid = True
        send_metric(item, valid)


def flag_in_else(rows):
    # The `else` sets the same name to the other constant. Reading only the
    # `if` body made this look settled when a later row can still unset it.
    flag = False
    for row in rows:
        if row.ok:
            flag = True
        else:
            flag = False
    return flag


def audit_in_else(rows, audit):
    # `audit` came from the caller, who can still see what the loop recorded.
    flag = False
    for row in rows:
        if row.ok:
            flag = True
        else:
            audit.record(row)
    return flag


def scan_grid(grid):
    # Settled inside the inner loop: one finding for the loop that can act on
    # it, not one per enclosing level. A `break` here leaves the inner loop.
    hit = False
    for row in grid:
        for cell in row:
            if cell.matches:
                hit = True
    return hit


def scan_after_inner_break(rows):
    # The `break` belongs to the inner loop and does not leave this one, so
    # this loop really does keep going after `hit` is settled.
    hit = False
    for row in rows:
        for cell in row:
            if cell is None:
                break
        if row.matches:
            hit = True
    return hit


def scan_with_nested_def(rows):
    # The `return` belongs to the nested function, not to this loop.
    hit = False
    for row in rows:
        def key(record):
            return record.id
        if row.matches:
            hit = True
    return hit


def walk_chain(head):
    # Mutates a set this function made and advances its own cursor. Both exist
    # to keep the loop going, which is exactly what the repair cuts, so this
    # stays a finding.
    visited = set()
    result = False
    while head:
        if head in visited:
            result = True
        visited.add(head)
        head = head.next
    return result
