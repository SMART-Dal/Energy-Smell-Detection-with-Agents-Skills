"""C1.S6 Unnecessary Initialization -- expensive setup before the check that
makes it unnecessary.

The card's first repair example. The finding's whole size is the hit rate, so
the two cases are a warm cache and a cold one: on a warm cache the setup was
paid and discarded every time, and on a cold one the repair is worth nothing.
Both readings belong on the card.
"""

def _load_defaults():
    return {f"key{i}": i for i in range(400)}


def before(cache, names):
    out = []
    for name in names:
        defaults = _load_defaults()
        if name in cache:
            out.append(cache[name])
        else:
            out.append({**defaults, "name": name}["name"])
    return out


def after(cache, names):
    out = []
    for name in names:
        if name in cache:
            out.append(cache[name])
        else:
            defaults = _load_defaults()
            out.append({**defaults, "name": name}["name"])
    return out


def cases():
    warm = {f"n{i}": f"n{i}" for i in range(500)}
    return [("warm-cache", lambda: (dict(warm), [f"n{i % 500}" for i in range(4_000)])),
            ("cold-cache", lambda: ({}, [f"m{i}" for i in range(4_000)])),
            ("edge",       lambda: ({}, []))]
