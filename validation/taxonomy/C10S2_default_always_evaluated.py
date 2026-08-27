"""C10.S2 Inefficient Built-in Choice -- `.get(k, default)`
evaluates the default whether or not it is needed.

`d.get(key, fallback)` instead of a membership test and a second subscript is the
description's own family of swaps, and `C4S8_membership_and_get` measures it at
+41.2%. One hash instead of two, one call instead of a branch.

That holds when the default is a value. Here it is a call, and Python evaluates
arguments before it enters `get`, so `_default_profile()` is built on every
lookup including the 95% that hit. The branch form built it only on the misses.
The faster built-in is being handed work the slower construct skipped.

The check is whether the second argument is an expression with a cost. `.get(k,
0)`, `.get(k, None)` and `.get(k, EMPTY)` are free; `.get(k, expensive())`,
`.get(k, [])` and `.get(k, Class())` are not, and `dict.setdefault` has exactly
the same problem.
"""

def _default_profile():
    return {f"field{i}": i for i in range(60)}


def before(profiles, keys):
    total = 0
    for key in keys:
        if key in profiles:
            profile = profiles[key]
        else:
            profile = _default_profile()          # built only on a miss
        total += profile["field1"]
    return total


def after(profiles, keys):
    total = 0
    for key in keys:
        profile = profiles.get(key, _default_profile())   # built every time
        total += profile["field1"]
    return total


def _profiles(n):
    return {i: {f"field{j}": j for j in range(60)} for i in range(n)}


def cases():
    return [("mostly-hit",  lambda: (_profiles(4_000), [i % 4_000 for i in range(40_000)])),
            ("mostly-miss", lambda: (_profiles(4_000), [i + 100_000 for i in range(40_000)])),
            ("edge",        lambda: (_profiles(4), []))]
