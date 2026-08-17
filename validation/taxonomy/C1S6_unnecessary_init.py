"""C1.S6 Unnecessary Initialization -- building a value the branch may not need."""

def before(rows, k):
    out = []
    for r in rows:
        fallback = [0] * 64        # built every time, used rarely
        out.append(r if r > k else fallback[0])
    return out


def after(rows, k):
    out = []
    for r in rows:
        if r > k:
            out.append(r)
        else:
            fallback = [0] * 64
            out.append(fallback[0])
    return out


def cases():
    return [("mostly-skipped", lambda: (list(range(200_000)), 10)),
            ("mostly-taken", lambda: (list(range(200_000)), 10**9)),
            ("empty", lambda: ([], 0))]
