"""C2.S3 Excessive Modularization in Hot Path -- a chain of thin layers.

From Javad's ObjectOriented/InternalGetterSetter. Three frames deep to read
one attribute, paid on every call.
"""

class Before:
    def __init__(self, name):
        self._name = name

    def _fetch(self):
        return self._get()

    def _get(self):
        return self._name

    def label(self):
        return self._fetch()


class After:
    def __init__(self, name):
        self._name = name

    def label(self):
        return self._name


def before(n):
    obj = Before("abc")
    total = 0
    for _ in range(n):
        total += len(obj.label())
    return total


def after(n):
    obj = After("abc")
    total = 0
    for _ in range(n):
        total += len(obj.label())
    return total


def cases():
    return [("hot", lambda: (300_000,)), ("cold", lambda: (20,))]
