"""Constructor calls in a default that build something no caller can mutate.

The shape here is exactly the one the rule matches -- a call evaluated once at
definition time and shared by every caller -- and it is fine, because the
object it produces is read-only.  `frozenset()`, `tuple()` and
`MappingProxyType()` are the three ways people write "a constant collection I
am deliberately sharing", and reporting them would train the reader to ignore
the rule on the calls that matter.

The inner `{...}` in the `MappingProxyType` default is a mutable literal, so
this also pins down that the rule looks at what the default *evaluates to*
rather than at any dict node it can find underneath.
"""

from __future__ import annotations

from types import MappingProxyType


def normalise_headers(headers, drop=frozenset({"connection", "keep-alive"})):
    """Strip hop-by-hop headers before forwarding a request."""
    return {name: value for name, value in headers.items() if name.lower() not in drop}


def build_query(table, columns=tuple(("id", "name"))):
    """Select a fixed set of columns unless the caller names others."""
    return f"SELECT {', '.join(columns)} FROM {table}"


def render_template(name, context=MappingProxyType({"title": "", "user": None})):
    """Render a template against a read-only default context."""
    return f"<{name}>" + "".join(f"{key}={value}" for key, value in context.items())
