"""C6.S7 Mutable Default Arguments -- the accumulation, where it is deliberate.

Writing this file settled something the card only asserted. The ordinary repair
-- replacing `seen=[]` with `seen=None` -- *changes behaviour*: the shared list
is the difference between the two versions, so `before` and `after` cannot be
compared and the equivalence check rejects them. That is not a limitation to
work around; it is the card being right that this is a correctness finding
whose energy cost is unbounded growth, and unbounded growth is not something a
one-second paired window can see.

What is measurable is the case the card sends to C8.S1: sharing that is
deliberate, done badly. Both variants here accumulate across calls and return
the same answers; only the shared structure differs, so the growing linear scan
is isolated from the semantics. If this pays and the `seen=None` version cannot
be measured at all, the card can say which of the two findings it is reporting.
"""

_SEEN_LIST = []
_SEEN_SET = set()


def _collect_list(item, seen=_SEEN_LIST):
    if item not in seen:                    # linear, and lengthens with use
        seen.append(item)
    return len(seen)


def _collect_set(item):
    _SEEN_SET.add(item)
    return len(_SEEN_SET)


def before(items):
    del _SEEN_LIST[:]
    total = 0
    for item in items:
        total += _collect_list(item)
    return total


def after(items):
    _SEEN_SET.clear()
    total = 0
    for item in items:
        total += _collect_set(item)
    return total


def cases():
    return [("many-distinct", lambda: (list(range(8_000)),)),
            ("few-distinct",  lambda: ([i % 20 for i in range(8_000)],)),
            ("edge",          lambda: ([],))]
