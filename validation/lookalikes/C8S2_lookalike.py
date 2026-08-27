"""C8.S2 Missing Derived-Value Reuse -- LOOKS THE SAME, IS NOT: the artefact is mutable
and the caller writes to it.

"Parse configuration files at module load time and store in a module-level
variable" is the description, and `C8S2_parsed_config_reused` measures it at
+100% -- with `after` handing back the shared object only because nothing in
that file mutates it.

Here the caller adds a per-request key to the config it is given. Parsing per
call gave every caller a private document; reusing one parsed dict gives them
all the same document, and the request-scoped keys accumulate in it. The first
call is right, the second sees the first one's overrides, and the totals drift
upward for the life of the process.

The clause is that the artefact must be safe to share, which for a compiled
regex or a `struct.Struct` is free -- they are immutable -- and for a parsed
document is a promise nobody made. Reuse it read-only, or hand out a copy, and
say which in the finding.
"""

import json

_RAW = json.dumps({f"key{i}": i for i in range(200)})
_PARSED = json.loads(_RAW)


def _handle(config, request):
    config[f"req{request % 7}"] = request          # request-scoped override
    return sum(config.values())


def before(requests):
    total = 0
    for request in requests:
        total += _handle(json.loads(_RAW), request)
    return total


def after(requests):
    total = 0
    for request in requests:
        total += _handle(_PARSED, request)         # one shared document
    return total


def cases():
    return [("many-requests", lambda: (list(range(4_000)),)),
            ("one-request",   lambda: ([1],)),
            ("edge",          lambda: ([],))]
