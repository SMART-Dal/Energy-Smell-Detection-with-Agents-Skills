"""C6.S3 Eager Materialisation -- a list comprehension handed straight to `sum`.

The card says materialising a list where a generator would do wastes memory
and time. Javad's ImproperDataStructure/SumMap1 claims the reverse for `sum`:
the list comprehension beats the generator expression.

If that holds, the exception is real and mechanical -- a genexp resumes a frame
per element, which for a cheap reducer costs more than the allocation it saves.
"""

def before(xs):
    return sum([x * 2 for x in xs])


def after(xs):
    return sum(x * 2 for x in xs)


def cases():
    return [
        ("large", lambda: (list(range(500_000)),)),
        ("small", lambda: (list(range(50)),)),
    ]
