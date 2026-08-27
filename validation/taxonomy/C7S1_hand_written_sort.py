"""C7.S1 Suboptimal Algorithm Choice -- naive substring search against KMP.

The third shape, and neither side calls a built-in: `str.find` would settle the
question in C and say nothing about the algorithm. `before` restarts the
comparison at the next character after a mismatch, which is quadratic on text
with long repeated runs; `after` reuses what the failed comparison already
proved, which is linear.

`sparse-text` is the case where the naive scan is competitive: a mismatch on the
first character costs one comparison, so the quadratic term never appears and
KMP is left paying for a prefix table nothing uses.
"""

def _naive_count(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return 0
    hits = 0
    for start in range(n - m + 1):
        k = 0
        while k < m and text[start + k] == pattern[k]:
            k += 1
        if k == m:
            hits += 1
    return hits


def _kmp_count(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return 0
    # Prefix table: failure[k] is the length of the longest proper prefix of
    # pattern[:k+1] that is also a suffix of it.
    failure = [0] * m
    length = 0
    for k in range(1, m):
        while length and pattern[k] != pattern[length]:
            length = failure[length - 1]
        if pattern[k] == pattern[length]:
            length += 1
        failure[k] = length
    hits = 0
    length = 0
    for character in text:
        while length and character != pattern[length]:
            length = failure[length - 1]
        if character == pattern[length]:
            length += 1
        if length == m:
            hits += 1
            length = failure[length - 1]
    return hits


def before(text, pattern):
    return _naive_count(text, pattern)


def after(text, pattern):
    return _kmp_count(text, pattern)


def cases():
    return [("repetitive-text", lambda: ("a" * 60_000, "a" * 40 + "b")),
            ("sparse-text",     lambda: ("abcdefgh" * 20_000, "xyz")),
            ("edge",            lambda: ("", "a"))]
