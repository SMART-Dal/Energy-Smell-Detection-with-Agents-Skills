"""C4.S3 Inefficient Conditional Nesting -- nesting that forced the same work
into three arms.

The file this replaces was a second copy of `C4S3_guard_clauses`: nested `if`s
against `continue`s, over `range(500_000)` where the `is not None` test could
never fail. Two of the three C4.S3 shapes were therefore the same experiment,
and one of them tested a condition with no false case.

This is the other half of what the description names -- "repeated checks on
overlapping conditions". The nesting is what makes `_normalise(entry)` appear in
three arms; flattening it computes the value once and dispatches on it. The
tests are the same tests and the answer is the same answer, so what the reading
shows is the duplicated call, not the indentation.

`already-flat` is the adversarial case the card needs: input on which the first
arm always wins means the duplicate never runs, and the flattening saves
nothing.
"""

def _normalise(entry):
    return entry["name"].strip().lower()


def before(entries, blocked, featured):
    kept = []
    for entry in entries:
        if entry["active"]:
            if _normalise(entry) in blocked:
                continue
            if _normalise(entry) in featured:
                kept.append(_normalise(entry).upper())
            else:
                kept.append(_normalise(entry))
    return kept


def after(entries, blocked, featured):
    kept = []
    for entry in entries:
        if not entry["active"]:
            continue
        name = _normalise(entry)
        if name in blocked:
            continue
        kept.append(name.upper() if name in featured else name)
    return kept


def _entries(n, active_ratio):
    step = max(1, int(1 / active_ratio)) if active_ratio else n + 1
    return [{"name": f"  Entry{i}  ", "active": i % step == 0} for i in range(n)]


def cases():
    blocked = {f"entry{i}" for i in range(0, 200_000, 97)}
    featured = {f"entry{i}" for i in range(0, 200_000, 53)}
    return [("mostly-active", lambda: (_entries(200_000, 1.0), set(blocked), set(featured))),
            ("already-flat",  lambda: (_entries(200_000, 0.02), set(blocked), set(featured))),
            ("edge",          lambda: ([], set(), set()))]
