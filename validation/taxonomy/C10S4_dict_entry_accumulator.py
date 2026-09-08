"""C10.S4 Inefficient String Concatenation -- the accumulator is a dict entry.

The card's second repair example. A subscript target is aliased through the
container, so the in-place resize cannot fire and the described O(N*M) copying
is what happens, per key. Two shapes of the same data: many keys with few parts
each, and few keys with many parts each -- since the card says the part count
per accumulator is what decides the size.
"""

def before(rows):
    out = {}
    for key, text in rows:
        out.setdefault(key, "")
        out[key] += text
    return out


def after(rows):
    parts = {}
    for key, text in rows:
        parts.setdefault(key, []).append(text)
    return {key: "".join(chunk) for key, chunk in parts.items()}


def _rows(keys, per_key):
    return [(f"k{k}", f"part{i}-") for k in range(keys) for i in range(per_key)]


def cases():
    return [("few-keys-many-parts", lambda: (_rows(20, 4_000),)),
            ("many-keys-few-parts", lambda: (_rows(20_000, 4),))]
