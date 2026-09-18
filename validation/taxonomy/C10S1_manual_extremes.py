"""C10.S1 Skipping Optimized Built-ins -- a hand-written min/max scan.

The taxonomy's own first example for this root cause, which had no
implementation: "writing a manual min/max scan with a loop and comparison when
the built-in min()/max() does the same in C".

Two C traversals beat one interpreted traversal, because the interpreted one
pays dispatch and reference counting per element and the builtins pay neither.

The original uses two independent `if`s rather than the `if/elif` the card
shows. With `elif` a new minimum can never also update the maximum, which is a
bug on the first element and would make the two variants disagree rather than
measure the same work.
"""


def before(values):
    smallest = values[0]
    largest = values[0]
    for x in values:
        if x < smallest:
            smallest = x
        if x > largest:
            largest = x
    return largest - smallest


def after(values):
    return max(values) - min(values)


def cases():
    return [("large",  lambda: ([(i * 7919) % 1_000_003 for i in range(600_000)],)),
            ("normal", lambda: ([(i * 7919) % 1_000_003 for i in range(6_000)],))]
