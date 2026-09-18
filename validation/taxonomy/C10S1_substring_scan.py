"""C10.S1 Manual Implementation of Built-ins -- a substring scan done by slicing.

The repair keeps the Python loop, which is the point the card makes with it:
what mattered was moving the per-element work into C, not removing the loop.

The original allocates a fresh string object for every position in the corpus
and recomputes `len(pattern)` each time; `str.find` scans in C and allocates
nothing. Every other measured file in this root cause replaces the loop itself,
so "same loop, cheaper body" has not been measured anywhere else.
"""


def before(corpus, pattern):
    found = []
    for i in range(len(corpus) - len(pattern) + 1):
        if corpus[i:i + len(pattern)] == pattern:
            found.append(i)
    return found


def after(corpus, pattern):
    found = []
    at = corpus.find(pattern)
    while at != -1:
        found.append(at)
        at = corpus.find(pattern, at + 1)
    return found


def cases():
    return [("rare-pattern",   lambda: ("abcdefgh" * 30_000, "hab")),
            ("common-pattern", lambda: ("abab" * 60_000, "ab"))]
