# Inputs for feed-split.py::split_text, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import importlib
import random
from html import escape

from bs4 import BeautifulSoup

split_text = importlib.import_module("feed-split").split_text

try:
    BeautifulSoup("<p>x</p>", "html5lib")
    _PARSER = "html5lib"
except Exception:
    _PARSER = "html.parser"


# --------------------------------------------------------------------------- #
# helpers to synthesise feed-like HTML documents
# --------------------------------------------------------------------------- #
_WORDS = (
    "query index data feed search result ranking score document cluster "
    "vector embedding token parse chunk header section body table list item "
    "link reference snippet content pipeline segment field value request "
    "response handler stream buffer record update insert delete merge "
    "shard replica latency throughput schema mapping analyzer filter facet"
).split()


def _sentence(rng, n):
    words = [rng.choice(_WORDS) for _ in range(n)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def _paragraph(rng, n_sent):
    return " ".join(_sentence(rng, rng.randint(4, 9)) for _ in range(n_sent))


def _headings_doc(rng, n_sections, paras=3):
    parts = ["<html><body>"]
    for i in range(n_sections):
        lvl = (i % 3) + 1
        parts.append(f"<h{lvl}>{_sentence(rng, 5)}</h{lvl}>")
        for _ in range(paras):
            parts.append(f"<p>{_paragraph(rng, 3)}</p>")
    parts.append("</body></html>")
    return "".join(parts)


def _lists_doc(rng, n_lists, items):
    parts = ["<html><body>"]
    for i in range(n_lists):
        if i % 4 == 0:
            parts.append(f"<h2>{_sentence(rng, 4)}</h2>")
        parts.append(f"<p>{_paragraph(rng, 2)}</p>")
        tag = "ol" if i % 2 else "ul"
        parts.append(f"<{tag}>")
        for j in range(items):
            r = rng.random()
            if r < 0.25:
                parts.append(
                    '<li>{0} <a href="http://example.com/{1}/{2}">{3}</a></li>'.format(
                        _sentence(rng, 6), i, j, _sentence(rng, 3)))
            elif r < 0.45:
                parts.append(
                    '<li><a href="http://example.com/{0}/{1}">{2}</a></li>'.format(
                        i, j, _sentence(rng, 4)))
            elif r < 0.60:
                parts.append(
                    "<li>{0}<ul><li>{1}</li><li>{2}</li><li>{3}</li></ul></li>".format(
                        _sentence(rng, 3), _sentence(rng, 4),
                        _sentence(rng, 4), _sentence(rng, 4)))
            else:
                parts.append(f"<li>{_sentence(rng, rng.randint(5, 12))}</li>")
        parts.append(f"</{tag}>")
    parts.append("</body></html>")
    return "".join(parts)


def _tables_doc(rng, n_tables, rows, cols, wrap=False):
    parts = ["<html><body>"]
    for t in range(n_tables):
        if t % 5 == 0:
            parts.append(f"<h2>{_sentence(rng, 4)}</h2>")
        if wrap:
            parts.append("<div>")
        parts.append("<table>")
        parts.append("<thead><tr>" + "".join(
            f"<th>{_sentence(rng, 2)}</th>" for _ in range(cols)) + "</tr></thead>")
        parts.append("<tbody>")
        for r in range(rows):
            cells = []
            for c in range(cols):
                rr = rng.random()
                if rr < 0.12:
                    cells.append(
                        '<td><a href="http://example.com/{0}/{1}/{2}">{3}</a></td>'.format(
                            t, r, c, _sentence(rng, 3)))
                elif rr < 0.20:
                    cells.append(
                        f'<td><img src="http://example.com/{r}.png"/></td>')
                else:
                    cells.append(f"<td>{_sentence(rng, rng.randint(3, 8))}</td>")
            parts.append("<tr>" + "".join(cells) + "</tr>")
        parts.append("</tbody></table>")
        if wrap:
            parts.append("</div>")
        parts.append(f"<p>{_paragraph(rng, 2)}</p>")
    parts.append("</body></html>")
    return "".join(parts)


def _code_doc(rng, n_blocks):
    parts = ["<html><body>"]
    for i in range(n_blocks):
        parts.append(f"<h2>{_sentence(rng, 4)}</h2>")
        parts.append(f"<p>{_paragraph(rng, 2)}</p>")
        kind = i % 3
        if kind == 0:
            body = ("{% highlight python %}\n"
                    + "\n".join(f"value_{j} = compute(data, {j})" for j in range(10))
                    + "\n{% endhighlight %}")
        elif kind == 1:
            body = ("\ncurl -X POST 'http://localhost:8080/api/v1/search' \\\n"
                    "  -H 'Content-Type: application/json' \\\n"
                    "  -d '{\"query\": \"sample\", \"hits\": 10}'")
        else:
            body = ("\nimport com.yahoo.search.Query;\n"
                    "import com.yahoo.search.Result;\n\n"
                    'Query query = new Query("sample");\n'
                    "Result result = searcher.search(query);")
        parts.append("<pre><code>" + escape(body) + "</code></pre>")
    parts.append("</body></html>")
    return "".join(parts)


def _plain_doc(rng, n_paragraphs):
    parts = ["<html><body>"]
    for i in range(n_paragraphs):
        parts.append(f"<p>{_paragraph(rng, 4)}</p>")
        if i % 20 == 5:
            parts.append("<ul>" + "".join(
                f"<li>{_sentence(rng, 6)}</li>" for _ in range(6)) + "</ul>")
    parts.append("</body></html>")
    return "".join(parts)


def _empty_sections_doc(rng, n):
    parts = ["<html><body>"]
    for i in range(n):
        lvl = (i % 6) + 1
        parts.append(f"<h{lvl}>{_sentence(rng, 4)}</h{lvl}>")
        if i % 7 == 3:
            parts.append(f"<p>{_paragraph(rng, 2)}</p>")
    parts.append("</body></html>")
    return "".join(parts)


def _mixed_doc(rng, n_sections):
    parts = ["<html><body>"]
    for i in range(n_sections):
        lvl = (i % 3) + 1
        parts.append(f"<h{lvl}>{_sentence(rng, 5)}</h{lvl}>")
        parts.append(f"<p>{_paragraph(rng, 3)}</p>")
        m = i % 4
        if m == 0:
            parts.append("<ul>" + "".join(
                '<li>{0} <a href="http://example.com/{1}/{2}">{3}</a></li>'.format(
                    _sentence(rng, 5), i, j, _sentence(rng, 3))
                for j in range(8)) + "</ul>")
        elif m == 1:
            parts.append("<table><tbody>" + "".join(
                "<tr>" + "".join(f"<td>{_sentence(rng, 4)}</td>" for _ in range(4))
                + "</tr>" for _ in range(6)) + "</tbody></table>")
        elif m == 2:
            parts.append("<pre><code>" + escape(
                "{% highlight python %}\n"
                + "\n".join(f"x_{j} = f({j})" for j in range(6))
                + "\n{% endhighlight %}") + "</code></pre>")
        else:
            parts.append(
                '<p><img src="http://example.com/{0}.png"/> {1}</p>'.format(
                    i, _paragraph(rng, 2)))
    parts.append("</body></html>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# documents built once, at import time
# --------------------------------------------------------------------------- #
_HTML = {
    "headings": _headings_doc(random.Random(0), 150),
    "lists": _lists_doc(random.Random(1), 50, 10),
    "tables": _tables_doc(random.Random(2), 16, 12, 4, wrap=False),
    "tables-div": _tables_doc(random.Random(3), 16, 12, 4, wrap=True),
    "code": _code_doc(random.Random(4), 80),
    "plain": _plain_doc(random.Random(5), 180),
    "empty-sections": _empty_sections_doc(random.Random(6), 220),
    "mixed": _mixed_doc(random.Random(7), 90),
}


def _soup(key):
    # split_text mutates the soup, so every thunk call gets a fresh parse
    return BeautifulSoup(_HTML[key], _PARSER)


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #
def checks():
    return [
        ("empty-body",
         lambda: (BeautifulSoup("<html><body></body></html>", _PARSER),)),
        ("single-heading",
         lambda: (BeautifulSoup("<html><body><h1>Only Header</h1></body></html>",
                                _PARSER),)),
        ("none-soup", lambda: (None,)),
    ]


def cases():
    return [
        ("many-headings",       lambda: (_soup("headings"),)),
        ("lists-and-links",     lambda: (_soup("lists"),)),
        ("top-level-tables",    lambda: (_soup("tables"),)),
        ("tables-inside-divs",  lambda: (_soup("tables-div"),)),
        ("code-blocks",         lambda: (_soup("code"),)),
        ("no-headings",         lambda: (_soup("plain"),)),
        ("consecutive-headings", lambda: (_soup("empty-sections"),)),
        ("mixed-large",         lambda: (_soup("mixed"),)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['mixed-large', 'lists-and-links', 'top-level-tables', 'tables-inside-divs']
_KEEP_CHECKS = ['empty-body', 'single-heading', 'none-soup']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
