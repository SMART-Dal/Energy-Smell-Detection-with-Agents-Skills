"""C4.S8 Non-Idiomatic Constructs -- `key in mapping.keys()` then a second
lookup.

Two changes the card separates: `key in mapping` skips building a view object,
and `.get()` replaces a membership test followed by a second hash of the same
key. The card says the third is the only one worth much, and this measures
both together because that is how the code is actually written.
"""

def before(mapping, keys):
    out = []
    for key in keys:
        if key in mapping.keys():
            out.append(mapping[key])
        else:
            out.append(None)
    return out


def after(mapping, keys):
    return [mapping.get(key) for key in keys]


def _mapping(n):
    return {f"k{i}": i for i in range(n)}


def cases():
    return [("mostly-hit",  lambda: (_mapping(50_000), [f"k{i}" for i in range(200_000)])),
            ("mostly-miss", lambda: (_mapping(50_000), [f"m{i}" for i in range(200_000)]))]
