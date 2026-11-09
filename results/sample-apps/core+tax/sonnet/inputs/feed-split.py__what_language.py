# Inputs for feed-split.py::what_language, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import importlib
import random

from bs4 import BeautifulSoup

what_language = importlib.import_module('feed-split').what_language

# Words that never contain "curl", "import com.yahoo" or "{%" so the filler
# cannot accidentally trigger any of the branches under test.
_WORDS = (
    "the quick brown fox jumps over a lazy dog while parsing markdown "
    "documents and extracting text blocks from html pages with data values "
    "sample repository feed splitter paragraph header table list note "
    "section content example output input format string number field"
).split()


def _filler(words, seed):
    rng = random.Random(seed)
    toks = [rng.choice(_WORDS) for _ in range(words)]
    for i in range(40, len(toks), 40):
        toks[i] = toks[i] + "\n"
    return " ".join(toks)


def _el(text):
    # A real BeautifulSoup element; the function only reads el.text.
    return BeautifulSoup(text, "html.parser")


# Built once at module level; the function never mutates its argument, so the
# same element can be handed to every repeated call.
_C1 = _el("{% highlight python %}\n" + _filler(30_000, 1))
_C2 = _el("{%   highlight   java   %}\n" + _filler(30_000, 2))
_C3 = _el(_filler(150_000, 3) + " curl -X POST https://api.example.com/data\n")
_C4 = _el(_filler(150_000, 4) + " import com.yahoo.platform.Foo;\n")
_C5 = _el(_filler(150_000, 5))
_C6 = _el("curl -X POST https://api.example.com/data\n" + _filler(150_000, 6))
_C7 = _el("run this: curl -O file\n" + _filler(150_000, 7)
          + " import com.yahoo.Bar;\n")
_C8 = _el(_filler(150_000, 8) + " {% highlight ruby %}\n" + _filler(20_000, 9))


def checks():
    return [
        ("empty", lambda: (_el(""),)),
        ("curl-at-index-zero", lambda: (_el("curl https://example.com"),)),
        ("no-space-before-percent", lambda: (_el("{%highlight python%}"),)),
    ]


def cases():
    return [
        ("highlight-python-at-start", lambda: (_C1,)),
        ("highlight-java-spaced", lambda: (_C2,)),
        ("curl-near-end", lambda: (_C3,)),
        ("java-near-end", lambda: (_C4,)),
        ("no-markers", lambda: (_C5,)),
        ("curl-at-index-zero-large", lambda: (_C6,)),
        ("both-markers", lambda: (_C7,)),
        ("highlight-not-at-start", lambda: (_C8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['highlight-not-at-start', 'no-markers', 'java-near-end', 'curl-at-index-zero-large']
_KEEP_CHECKS = ['empty', 'curl-at-index-zero', 'no-space-before-percent']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
