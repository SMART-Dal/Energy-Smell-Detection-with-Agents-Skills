"""C10.S2 Suboptimal Built-in Choice -- a literal prefix matched with a regex.

The pattern has no metacharacters beyond the anchor, so the regex engine's
state machine is pure overhead. Even with the module cache warm, `re.match`
hashes the pattern, probes the cache, enters the matcher and allocates a match
object; `startswith` compares bytes and returns a bool.

The precondition is the whole finding: the moment the pattern has a
metacharacter the repair does not exist. `anchored-literal` is the case it
holds for, and `needs-the-engine` uses a pattern that genuinely needs matching,
where the two are the same call and the repair is unavailable.
"""

import re

_PREFIX = re.compile(r"^10\.")
_GENERAL = re.compile(r"^10\.\d+\.")


def before(hosts, general):
    pattern = _GENERAL if general else _PREFIX
    return sum(1 for host in hosts if pattern.match(host) is not None)


def after(hosts, general):
    if general:
        return sum(1 for host in hosts if _GENERAL.match(host) is not None)
    return sum(1 for host in hosts if host.startswith("10."))


def _hosts(n):
    return [f"10.{i % 256}.0.1" if i % 3 else f"192.168.{i % 256}.1"
            for i in range(n)]


def cases():
    return [("anchored-literal", lambda: (_hosts(400_000), False)),
            ("needs-the-engine", lambda: (_hosts(400_000), True))]
