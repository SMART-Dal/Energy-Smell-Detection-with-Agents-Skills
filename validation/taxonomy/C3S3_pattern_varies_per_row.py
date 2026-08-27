"""C3.S3 Inefficient Per-Iteration Setup -- the pattern is
built from the row.

`re.compile` inside a loop is the canonical instance and
`C3S3_regex_compiled_per_iteration` measures hoisting it at +44.6%. The shape
here is the same call in the same position.

What varies is the argument. The pattern is derived from the row, so there is
no single object to hoist; the mechanical repair is a dict of compiled patterns
built as they are needed. On input where the rows repeat that is a real cache
and it wins. On input where each row is distinct it is a dict insert, a hash and
a miss per row, on top of the compile that still happens -- and `re` already
keeps its own compiled-pattern cache, so the compile the loop appeared to be
paying was mostly a dict probe to begin with.

Hoist a derived artefact only when the thing it is derived from is the same
every time. Otherwise the question is the hit rate, which is C8.S1.
"""

import re


def before(rows):
    hits = 0
    for prefix, text in rows:
        if re.search(rf"\b{prefix}\d+", text):
            hits += 1
    return hits


def after(rows):
    compiled = {}
    hits = 0
    for prefix, text in rows:
        pattern = compiled.get(prefix)
        if pattern is None:
            pattern = compiled[prefix] = re.compile(rf"\b{prefix}\d+")
        if pattern.search(text):
            hits += 1
    return hits


def cases():
    return [("all-distinct", lambda: ([(f"p{i}", f"p{i}42 and more text") for i in range(20_000)],)),
            ("few-distinct", lambda: ([(f"p{i % 20}", f"p{i % 20}42 and more text") for i in range(20_000)],)),
            ("edge",         lambda: ([],))]
