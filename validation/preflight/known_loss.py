"""The same pair as known_saving.py with the variants swapped.

The measured number must change sign. A rig that reports a saving in both
directions is measuring something other than the code.
"""

import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from known_saving import after as _fast, before as _slow

before = _fast
after = _slow


def cases():
    return [("hash-vs-linear", lambda: (list(range(5_000)), list(range(0, 5_000, 5))))]
