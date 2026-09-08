"""C8.S2 Missing Derived-Value Reuse -- a regex compiled on every call."""

import re

_PATTERN = re.compile(r"^tmp_\d+$")


def before(names):
    return sum(1 for n in names if re.match(r"^tmp_\d+$", n))


def after(names):
    return sum(1 for n in names if _PATTERN.match(n))


def cases():
    names = [f"tmp_{i}" if i % 2 else f"keep_{i}" for i in range(100_000)]
    return [("large", lambda: (list(names),)),
            ("small", lambda: (names[:20],))]
