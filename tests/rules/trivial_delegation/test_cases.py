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
