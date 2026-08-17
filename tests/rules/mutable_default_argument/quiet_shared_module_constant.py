"""A module-level mutable bound by name in the default: the boundary.

`DEFAULT_LIMITS` really is a mutable object shared by every caller, so this is
the same latent bug -- but the rule claims a *syntactic* fact, "the default
expression constructs a mutable object", and here the default expression is a
name.  Following the name would mean deciding what it is bound to at every
point in the module, and the common case is a constant that the whole codebase
treats as read-only, so following it would trade one certain report for a pile
of contextual ones.  Ruff's B006 draws the line in the same place.

The recall this gives up is stated here on purpose: if the rule ever starts
resolving names, this case is where that decision gets argued.
"""

from __future__ import annotations

DEFAULT_LIMITS = {"requests": 100, "burst": 20}
DEFAULT_STAGES = ["fetch", "parse", "store"]


def throttle(client, limits=DEFAULT_LIMITS):
    """Apply rate limits to a client."""
    return client.with_limits(limits["requests"], limits["burst"])


def run_pipeline(source, stages=DEFAULT_STAGES):
    """Run the named stages over one source."""
    for stage in stages:
        source = source.apply(stage)
    return source
