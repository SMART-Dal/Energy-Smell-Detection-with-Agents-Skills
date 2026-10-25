"""Cases for mutable_default_argument."""

import collections
from collections import Counter
from datetime import datetime


def collect_samples(value, seen=[]):
    # The card's own example: one list, shared by every call that omits it.
    seen.append(value)
    return seen


class Registry:
    def register(self, name, tags=set(), aliases=[]):
        # Two mutable defaults on one signature, so two separate findings.
        tags.add(name)
        aliases.append(name)
        return self


def tally_words(words, *, counts=Counter()):
    # Keyword-only default: same mechanism, a different slot in the AST.
    for word in words:
        counts[word] += 1
    return counts


def build_index(records, index=collections.defaultdict(list)):
    # Same constructor reached through its module rather than imported bare.
    for record in records:
        index[record.key].append(record)
    return index


def memoised_fib(n, memo={0: 0, 1: 1}):
    # Sharing is load-bearing here; reported anyway, since no analyzer can read
    # intent and the reader needs to see the retention before excusing it.
    if n not in memo:
        memo[n] = memoised_fib(n - 1, memo) + memoised_fib(n - 2, memo)
    return memo[n]


def make_collector(prefix):
    # The inner signature owns the default; the enclosing unit must stay quiet.
    def collect(value, seen=[]):
        seen.append(f"{prefix}{value}")
        return seen

    return collect


def render(items, separator=", ", limits=(0, 100)):
    # A tuple default is shared too, and nothing can change it.
    return separator.join(str(i) for i in items[limits[0]:limits[1]])


def parse_options(text, overrides=None):
    # The repair itself: the mutable object is built per call, in the body.
    options = {}
    for line in text.splitlines():
        key, _, value = line.partition("=")
        options[key.strip()] = value.strip()
    options.update(overrides or {})
    return options


def stamp_event(event, at=datetime.now(), tags=frozenset()):
    # `datetime.now()` is frozen at import, which is a bug about *when* the
    # default is evaluated, not about mutating it; a frozenset cannot grow.
    event.recorded_at = at
    event.tags = tags | {"stamped"}
    return event


def build_widget(title, state=config_builder.set("initialized", True)):
    # `.set()` is a builder method, not the `set` constructor. Matching on the
    # final attribute alone read every fluent API in a signature as a shared
    # mutable default.
    return title, state


def batch_process(factors=[2 ** i for i in range(8)],
                  mapping={k: [] for k in ("a", "b")}):
    # A comprehension in a default runs once at definition time and hands
    # every call the same object, exactly as `[]` does.
    factors.append(99)
    return mapping


def is_allowed(scope, allowed=["read", "write"]):
    # Only read: nothing accumulates, and the card measured the `None` repair
    # as costing more.
    return scope in allowed


def app_describe(object_id, input_params={}, always_retry=True, **kwargs):
    # dx-toolkit's generated wrappers: handed to a call in another module that
    # only serialises it. Not followed, so not reported.
    return DXHTTPRequest("/%s/describe" % object_id, input_params,
                         always_retry=always_retry, **kwargs)


def normalise(rows, out=[]):
    # Rebound to a copy before anything changes it: the default itself stays empty.
    out = list(out)
    out.extend(rows)
    return out


def snapshot(state, history=[]):
    # Returned: the caller holds the shared object and whatever it adds stays.
    return history


def _visit(node, seen):
    seen.add(node)


def walk(node, seen=set()):
    # Changed in a helper of this module, which is where it fills up.
    _visit(node, seen)
    return len(seen)


def summarise(values, totals={}):
    # Handed to a helper of this module that only reads it.
    return _count(values, totals)


def _count(values, totals):
    return sum(totals.get(v, 0) for v in values)


class Cache:
    def __init__(self, entries={}):
        # Stored on the instance: every Cache made without entries shares one dict.
        self.entries = entries


class Collector:
    def gather(self, item, bucket=[]):
        # The method it calls appends.
        self._fill(bucket, item)
        return len(bucket)

    def _fill(self, bucket, item):
        bucket.append(item)
