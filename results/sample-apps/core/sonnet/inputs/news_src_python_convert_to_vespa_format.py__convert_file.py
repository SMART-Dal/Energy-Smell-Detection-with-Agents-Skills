# Inputs for news/src/python/convert_to_vespa_format.py::convert_file, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import io
import random

from convert_to_vespa_format import convert_file

# ---------------------------------------------------------------------------
# Module-level input construction (never timed).
# ---------------------------------------------------------------------------

_R = random.Random(0)
_VOCAB = [
    "".join(_R.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(_R.randint(3, 14)))
    for _ in range(3000)
]
_CATS = ["sports", "business", "technology", "health", "music", "news",
         "travel", "food", "science", "politics"]
_SUBS = ["a", "b", "c", "d", "e"]


def _text(rng, nwords):
    return " ".join(rng.choice(_VOCAB) for _ in range(nwords))


def _entities(rng, n):
    parts = []
    for _ in range(n):
        parts.append('{"id": "%s", "confidence": %.3f}'
                     % (rng.choice(_VOCAB), rng.random()))
    return "[" + ", ".join(parts) + "]"


def _rows(n, seed, dup_ratio=0.0, title_words=6, abstract_words=25, n_entities=3):
    rng = random.Random(seed)
    rows = []
    unique = []
    for i in range(n):
        if unique and rng.random() < dup_ratio:
            nid = unique[rng.randrange(len(unique))]
        else:
            nid = "N%07d" % i
            unique.append(nid)
        rows.append([
            nid,
            rng.choice(_CATS),
            rng.choice(_SUBS),
            _text(rng, title_words),
            _text(rng, abstract_words),
            "https://example.com/%d" % rng.randrange(10 ** 9),
            _entities(rng, n_entities),
            _entities(rng, n_entities + rng.randint(0, 5)),
        ])
    return rows


def _write(path, rows):
    with io.open(str(path), "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r))
            f.write("\n")


def _click_map(rows, seed):
    rng = random.Random(seed)
    cm = {}
    for r in rows:
        cm[r[0]] = {"clicks": rng.randint(0, 200),
                    "impressions": rng.randint(0, 20000)}
    return cm


def _make(name, n, seed, dup_ratio=0.0, title_words=6, abstract_words=25,
          n_entities=3, prepopulate=0):
    rows = _rows(n, seed, dup_ratio, title_words, abstract_words, n_entities)
    path = str(WORKDIR / ("news_%s.tsv" % name))
    _write(path, rows)
    cm = _click_map(rows, seed + 1000)
    pre = [r[0] for r in rows[:prepopulate]]

    def thunk():
        random.seed(424242)          # make generate_random_date deterministic
        return (io.StringIO(), path, set(pre), cm)

    return thunk


_CASES = [
    ("baseline-2k", _make("baseline", 2000, 1)),
    ("large-8k", _make("large", 8000, 2)),
    ("duplicates", _make("dups", 8000, 3, dup_ratio=0.5)),
    ("prepopulated-half", _make("prepop", 9000, 4, prepopulate=4500)),
    ("long-text", _make("long", 3000, 5, title_words=60, abstract_words=300,
                        n_entities=8)),
    ("short-text-8k", _make("short", 8000, 6, title_words=2, abstract_words=4,
                            n_entities=0)),
    ("entity-heavy", _make("ents", 5000, 7, n_entities=40)),
    ("mixed", _make("mixed", 8000, 8, dup_ratio=0.3, prepopulate=2000,
                    title_words=15, abstract_words=80)),
]

# ---------------------------------------------------------------------------
# Edge inputs for checks().
# ---------------------------------------------------------------------------

_EMPTY_PATH = str(WORKDIR / "news_empty.tsv")
_write(_EMPTY_PATH, [])

_ONE_ROWS = _rows(1, 999)
_ONE_PATH = str(WORKDIR / "news_one.tsv")
_write(_ONE_PATH, _ONE_ROWS)
_ONE_CM = _click_map(_ONE_ROWS, 999)

_MISSING_PATH = str(WORKDIR / "news_definitely_missing.tsv")


def _empty_thunk():
    random.seed(1)
    return (io.StringIO(), _EMPTY_PATH, set(), {})


def _one_thunk():
    random.seed(1)
    return (io.StringIO(), _ONE_PATH, set(), _ONE_CM)


def _missing_thunk():
    random.seed(1)
    return (io.StringIO(), _MISSING_PATH, set(), {})


def checks():
    return [
        ("empty-file", _empty_thunk),
        ("single-row", _one_thunk),
        ("missing-file", _missing_thunk),
    ]


def cases():
    return list(_CASES)


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['large-8k', 'entity-heavy', 'short-text-8k', 'long-text']
_KEEP_CHECKS = ['empty-file', 'single-row', 'missing-file']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
