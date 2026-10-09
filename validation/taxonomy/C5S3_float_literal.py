"""C5.S3 Over-Provisioned Data Type -- a float literal on integer data.

From Javad's ImproperDataStructure/MultiplyByFactor. An integer multiply keeps
small-int caching and avoids boxing a float per element; `3.0` gives up both
for a value with no fractional part.
"""

def before(xs):
    return [x * 3.0 for x in xs]


def after(xs):
    return [x * 3 for x in xs]


def cases():
    return [
        ("large", lambda: (list(range(500_000)),)),
        ("small", lambda: (list(range(50)),)),
    ]
