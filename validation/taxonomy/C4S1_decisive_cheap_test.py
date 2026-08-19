"""C4.S1 Suboptimal Condition Order -- the cheap test decides most inputs.

The card says the saving is the expensive operand's cost times how often the
cheap test short-circuits, so the two cases put that fraction on either side:
`mostly-unpublished` lets the attribute read settle 90% of rows, and
`mostly-published` lets it settle almost none. The first should pay and the
second should not, and the gap is the finding.
"""

def _permitted(viewer, row):
    return sum(ord(c) for c in row["owner"]) % 7 == viewer % 7


def before(rows, viewer):
    return [r for r in rows if _permitted(viewer, r) and r["published"]]


def after(rows, viewer):
    return [r for r in rows if r["published"] and _permitted(viewer, r)]


def _rows(n, published_ratio):
    step = max(1, int(1 / published_ratio)) if published_ratio else n + 1
    return [{"owner": f"owner-{i}", "published": (i % step == 0)} for i in range(n)]


def cases():
    return [("mostly-unpublished", lambda: (_rows(200_000, 0.1), 3)),
            ("mostly-published",   lambda: (_rows(200_000, 1.0), 3)),
            ("edge",               lambda: ([], 3))]
