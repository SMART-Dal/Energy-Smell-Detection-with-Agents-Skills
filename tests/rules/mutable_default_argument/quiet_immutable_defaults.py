"""Defaults that cannot accumulate state, so there is nothing to report.

Tuples, strings, numbers, `None` and booleans are shared between calls too --
the difference is that no caller can change them, so the sharing is invisible.
A rule that reported "a default object is reused" rather than "a *mutable*
default object is reused" would fire on almost every function in a codebase,
which is the failure mode this case exists to prevent.
"""

from __future__ import annotations


def paginate(query, page=0, size=50, order=("created_at", "id"), cursor=None):
    """Page through a query with a fixed default ordering."""
    offset = page * size
    return query.order_by(*order).offset(offset).limit(size)


def slugify(title, separator="-", strip=True, unicode_ok=False):
    """Reduce a title to a URL slug."""
    text = title.strip() if strip else title
    words = text.lower().split()
    return separator.join(word if unicode_ok else word.encode("ascii", "ignore").decode() for word in words)
