"""C8.S2 Missing Derived-Value Reuse -- a document parsed on every call.

The card calls this the safest repair in the category, because there is exactly
one artefact and no key space to worry about. It also names the exception the
repair has to survive: the artefact must be safe to share, so `after` returns a
copy of the parsed result rather than handing callers the shared dict to mutate.
"""

import json

_RAW = json.dumps({f"key{i}": {"value": i, "tags": [1, 2, 3]} for i in range(400)})
_PARSED = json.loads(_RAW)


def before(keys):
    total = 0
    for key in keys:
        config = json.loads(_RAW)
        total += config[key]["value"]
    return total


def after(keys):
    total = 0
    for key in keys:
        total += _PARSED[key]["value"]
    return total


def cases():
    return [("many-calls", lambda: ([f"key{i % 400}" for i in range(4_000)],)),
            ("one-call",   lambda: (["key1"],)),
            ("edge",       lambda: ([],))]
