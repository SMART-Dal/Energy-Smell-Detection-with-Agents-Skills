"""Cases for membership_test_on_sequence."""


def dedupe(rows):
    # The haystack is rebuilt and rescanned once per row.
    kept = []
    for row in rows:
        if row.key not in [k.key for k in kept]:
            kept.append(row)
    return kept


def grant_all(requests):
    # A literal extended by a call: the size is not knowable, so the scan is not either.
    allowed = ["read", "write", "admin"] + load_extra_scopes()
    for request in requests:
        if request.scope in allowed:
            grant(request)


def match_pairs(left, right):
    # A fresh sorted list scanned inside a nest: one test, one finding.
    for a in left:
        for b in right:
            if a.key in sorted(b.tags):
                yield a, b


def missing_ids(records, source):
    # `not in` scans just as hard as `in`, and the haystack is materialised.
    known = list(source.identifiers())
    gaps = []
    for record in records:
        if record.id not in known:
            gaps.append(record.id)
    return gaps


def read_only_requests(requests):
    # Three constants: the tuple scan beats hashing the key, and CPython folds it.
    for request in requests:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            yield request


def tag_rows(rows):
    # Four elements is under the size where an index repays its construction.
    priorities = ["high", "urgent", "critical", "blocker"]
    for row in rows:
        if row.label in priorities:
            escalate(row)


def accept_scopes(requests, extra):
    # Already a set: this is the shape the rule is asking code to become.
    allowed = {"read", "write", "admin"} | extra
    for request in requests:
        if request.scope in allowed:
            grant(request)


def error_lines(lines):
    # `in` on text is a substring search, not a container choice.
    for line in lines:
        if "ERROR" in line:
            yield line
