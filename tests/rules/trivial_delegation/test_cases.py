"""Cases for trivial_delegation."""

import functools


class Store:
    def fetch(self, key):
        # Pure forwarding: same argument, nothing added.
        return self._backend.fetch(key)

    def get(self, key, default=None):
        # A public alias that supplies a default is not pure forwarding.
        return self._backend.fetch(key) or default

    def load(self, key):
        # Adds a keyword the caller did not pass.
        return self._backend.fetch(key, strict=True)

    def read(self, key):
        # Translates the failure; the wrapper is the error boundary.
        try:
            return self._backend.fetch(key)
        except KeyError:
            return None

    def count(self):
        # Forwards with no arguments at all.
        return self._backend.count()

    @functools.lru_cache(maxsize=8)
    def cached(self, key):
        # Decorated: the wrapper is where the cache lives.
        return self._backend.fetch(key)

    def __len__(self):
        # A dunder keeps its signature.
        return self._backend.count()

    def swapped(self, first, second):
        # The arguments are reordered, so this is not a pass-through.
        return self._backend.pair(second, first)


def parse(text):
    # A module-level pure forwarder.
    return json_loads(text)


class Report:
    def __init__(self, rows):
        self._rows = rows
        self._size = None

    @property
    def size(self):
        # Computes and memoises on first access: `report._size` is None until
        # something has read `report.size`.
        if self._size is None:
            self._size = len(self._rows)
        return self._size


def concatenate(strings):
    # The separator is a choice this function makes, so it is not pure forwarding.
    return "".join(strings)


class Proxy:
    def route_event(self, *args, **kwargs):
        # How forwarding is written when the signature is not being restated.
        # `*args` unparses to a `Starred` and `**kwargs` lands in
        # `call.keywords` with no name, so a positional match could not see it.
        return self._dispatcher.route_event(*args, **kwargs)
