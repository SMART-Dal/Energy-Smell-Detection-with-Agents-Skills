"""C4.S8 Non-Idiomatic Condition -- `len(x) == 0` where truthiness would do.

The taxonomy's own first example for this root cause, which had no
implementation: `if len(my_list) == 0` against `if not my_list`.

`len()` is a global lookup, a call, and an integer comparison; the truth test
asks the object for its boolean directly and a list answers from its own size
field. The measured file for this root cause compares `in d.keys()` against
`in d`, which is a different mechanism -- building a view object rather than
resolving a builtin.

`mixed` is the case the repair is for. `always-empty` is here because the two
forms disagree about nothing and the saving is the same either way, which is
what makes this a pure idiom finding rather than a data-dependent one.
"""


def before(batches):
    empty = 0
    for batch in batches:
        if len(batch) == 0:
            empty += 1
    return empty


def after(batches):
    empty = 0
    for batch in batches:
        if not batch:
            empty += 1
    return empty


def cases():
    mixed = [[] if i % 3 == 0 else [1, 2, 3] for i in range(400_000)]
    return [("mixed",        lambda: (list(mixed),)),
            ("always-empty", lambda: ([[] for _ in range(400_000)],))]
