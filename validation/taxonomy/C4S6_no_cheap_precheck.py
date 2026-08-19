"""C4.S6 Exception-Driven Control Flow -- a raise with no cheap pre-check.

The card's first `NOT a smell when` clause. Checking membership first does not
remove the exception -- the key can be absent for a second reason the check
cannot see -- so the `try` stays and the check is pure extra cost. Expected to
read as a loss whatever the raise rate, which is what makes it the useful
adversarial case for this root cause.
"""

class Registry:
    __slots__ = ("_data",)

    def __init__(self, data):
        self._data = data

    def load(self, key):
        value = self._data[key]          # may raise KeyError
        if value < 0:
            raise KeyError(key)          # ... and may raise for a second reason
        return value


def before(registry, keys):
    out = []
    for key in keys:
        try:
            out.append(registry.load(key))
        except KeyError:
            out.append(None)
    return out


def after(registry, keys):
    out = []
    for key in keys:
        if key in registry._data:
            try:
                out.append(registry.load(key))
            except KeyError:
                out.append(None)
        else:
            out.append(None)
    return out


def _registry(n):
    return Registry({i: (i if i % 4 else -1) for i in range(n)})


def cases():
    return [("mostly-present", lambda: (_registry(200_000), list(range(200_000)))),
            ("mostly-missing", lambda: (_registry(200_000), list(range(400_000, 600_000)))),
            ("edge",           lambda: (_registry(4), []))]
