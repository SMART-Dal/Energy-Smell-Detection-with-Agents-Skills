"""Cases for membership_test_on_sequence."""

# Where a table of allowed values usually lives: above the function, not in it.
BLOCKED_AGENTS = [
    "curl", "wget", "python-requests", "scrapy", "httpie", "libwww",
    "java", "go-http-client", "okhttp", "axios", "postman", "insomnia",
    "bot", "crawler",
]
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


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


def reject_agents(requests):
    # The haystack is a module constant, which the unit never assigns.
    return [r for r in requests if r.agent in BLOCKED_AGENTS]


def audit_methods(requests):
    # A module constant short enough that the scan beats hashing.
    for request in requests:
        if request.method in SAFE_METHODS:
            yield request


def local_wins(requests):
    # A local of the same name shadows the module constant, and it is short.
    BLOCKED_AGENTS = ("curl", "wget")
    return [r for r in requests if r.agent in BLOCKED_AGENTS]


def check_one(agent):
    # Outside any repetition: one scan is not a smell.
    return agent in BLOCKED_AGENTS


def count_unique(lst):
    # The haystack is seeded empty and appended to, so it is N long by the end.
    unique = []
    for item in lst:
        if item not in unique:
            unique.append(item)
    return len(unique)


def filter_allowed(items, pool: list):
    # An annotation is a statement about what the value is.
    kept = []
    for item in items:
        if item in pool:
            kept.append(item)
    return kept


def route(requests):
    # A short literal that is never added to: scanning it beats hashing.
    for request in requests:
        if request.method in SAFE_METHODS:
            handle(request)


def dedupe_with_set(rows):
    # Already the repair.
    seen = set()
    for row in rows:
        if row not in seen:
            seen.add(row)
