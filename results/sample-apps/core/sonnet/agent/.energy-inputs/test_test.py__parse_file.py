# Inputs for test/test.py::parse_file, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

from bs4 import BeautifulSoup
from bs4.element import NavigableString, ProcessingInstruction


def _lines(n, seed, line_len=80):
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:()[]{}"
    return ["".join(rng.choice(alphabet) for _ in range(line_len)) for _ in range(n)]


def _contents(html):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("div")
    return list(tag.contents)


def _insert_pis(contents, count, seed):
    rng = random.Random(seed)
    out = list(contents)
    for i in range(count):
        out.insert(rng.randrange(len(out) + 1), ProcessingInstruction("php echo %d;" % i))
    return out


def _spans_html(n):
    return "<div>" + "".join("<span>value %d</span>" % i for i in range(n)) + "</div>"


def _nested_html(n):
    return "<div>" + "".join("<p><b>item %d</b><i>value %d</i></p>" % (i, i) for i in range(n)) + "</div>"


def _comments_html(n):
    return "<div>" + "".join("<!-- comment %d -->" % i for i in range(n)) + "</div>"


def _mixed_html(n, seed):
    rng = random.Random(seed)
    parts = []
    for i in range(n):
        r = rng.random()
        if r < 0.4:
            parts.append("<span class='s%d'>value %d</span>" % (i, i))
        elif r < 0.7:
            parts.append("<!-- comment %d -->" % i)
        else:
            parts.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(rng.randint(20, 80))))
    return "<div>" + "".join(parts) + "</div>"


# ---- module level inputs (built once, never timed) ----

_SMALL_PLAIN = (
    _contents("<div>" + "\n".join(_lines(40, 0, 50)) + "</div>"),
    {"data-path": "index.html"},
)

_PLAIN_LARGE = (
    _contents("<div>" + "\n".join(_lines(6000, 1, 80)) + "</div>"),
    {"data-path": "pages/main.html"},
)

_MANY_SPANS = (
    _contents(_spans_html(10000)),
    {"data-path": "templates/spans.html"},
)

_NESTED = (
    _contents(_nested_html(3000)),
    {"data-path": "templates/nested.html"},
)

_MANY_COMMENTS = (
    _contents(_comments_html(10000)),
    {"data-path": "templates/comments.html"},
)

_MANY_PIS = (
    _insert_pis(_contents("<div>" + "\n".join(_lines(200, 5, 60)) + "</div>"), 8000, 6),
    {"data-path": "templates/pis.html"},
)

_LEADING_NL = (
    _contents("<div>\n" + "\n".join(_lines(5000, 7, 60)) + "</div>"),
    {"data-path": "pages/leading.html"},
)

_MIXED = (
    _insert_pis(_contents(_mixed_html(12000, 8)), 300, 9),
    {"data-path": "mixed/page.html"},
)


def checks():
    return [
        ("missing-data-path", lambda: ([NavigableString("hello")], {})),
        ("absolute-path", lambda: ([NavigableString("hello")], {"data-path": "/etc/passwd"})),
        ("dotdot-path", lambda: ([NavigableString("hello")], {"data-path": "a/../b"})),
    ]


def cases():
    return [
        ("small-plain", lambda: _SMALL_PLAIN),
        ("plain-large", lambda: _PLAIN_LARGE),
        ("many-spans", lambda: _MANY_SPANS),
        ("nested-tags", lambda: _NESTED),
        ("many-comments", lambda: _MANY_COMMENTS),
        ("many-pis", lambda: _MANY_PIS),
        ("leading-newline", lambda: _LEADING_NL),
        ("mixed", lambda: _MIXED),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-pis', 'many-comments', 'leading-newline', 'plain-large']
_KEEP_CHECKS = ['missing-data-path', 'absolute-path', 'dotdot-path']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
