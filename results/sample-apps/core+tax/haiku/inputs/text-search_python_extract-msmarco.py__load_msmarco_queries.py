# Inputs for text-search/python/extract-msmarco.py::load_msmarco_queries, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import gzip
import importlib
import random

# Import the repository module exactly as the task specifies.
_MOD = importlib.import_module('extract-msmarco')

_BASE = WORKDIR / "msmarco_queries"

_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "what", "is", "capital", "of", "france", "how", "to", "make",
    "pasta", "best", "movie", "2023", "weather", "new", "york",
    "python", "programming", "language", "data", "science", "machine",
    "learning", "artificial", "intelligence", "neural", "network",
    "computer", "algorithm", "database", "security", "hello", "world",
    "example", "test", "query", "search", "engine", "information",
    "retrieval", "ranking", "evaluation", "performance", "system",
    "user", "interface", "design", "pattern", "architecture",
]

_PUNCT = list("!@#$%^&*()_+-=[]{};':\",./<>?\\|`~")

_UNICODE_WORDS = [
    "café", "naïve", "München", "Москва", "Ελλάδα", "北京", "こんにちは",
    "안녕하세요", "résumé", "façade", "jalapeño", "über", "señor",
    "😀", "🎉", "🚀", "❤️", "日本", "中国", "España", "Français",
    "Ünïcödé", "test123", "hello_world", "foo_bar",
]


def _gen_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(1, 4)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.3:
            q += "?"
        if rng.random() < 0.2:
            q = q.capitalize()
        lines.append((qid, q))
    return lines


def _gen_medium(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(5, 15)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.5:
            q += rng.choice([".", "?", "!", ","])
        if rng.random() < 0.3:
            pos = rng.randint(0, len(q) - 1)
            q = q[:pos] + "," + q[pos:]
        lines.append((qid, q))
    return lines


def _gen_long(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        target_len = rng.randint(500, 3000)
        parts = []
        total = 0
        while total < target_len:
            w = rng.choice(_WORDS)
            parts.append(w)
            total += len(w) + 1
            if rng.random() < 0.1:
                parts.append(rng.choice(_PUNCT))
        q = " ".join(parts)
        lines.append((qid, q))
    return lines


def _gen_punct(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 10)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        chars = list(q)
        for _ in range(rng.randint(5, 20)):
            pos = rng.randint(0, len(chars))
            chars.insert(pos, rng.choice(_PUNCT))
        q = "".join(chars)
        lines.append((qid, q))
    return lines


def _gen_upper(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_WORDS).upper() for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines


def _gen_unicode(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_UNICODE_WORDS) for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines


def _gen_empty_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        r = rng.random()
        if r < 0.1:
            q = ""
        elif r < 0.3:
            q = rng.choice([" ", "  ", "   "])
        elif r < 0.5:
            q = rng.choice("abcdefghijklmnopqrstuvwxyz")
        else:
            k = rng.randint(1, 3)
            q = " ".join(rng.choice(_WORDS) for _ in range(k))
        lines.append((qid, q))
    return lines


def _gen_huge(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(4, 12)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.4:
            q += "?"
        lines.append((qid, q))
    return lines


_WRITE_SPEC = [
    ("short", _gen_short, 20_000, 0),
    ("medium", _gen_medium, 40_000, 1),
    ("long", _gen_long, 5_000, 2),
    ("punct", _gen_punct, 30_000, 3),
    ("upper", _gen_upper, 30_000, 4),
    ("unicode", _gen_unicode, 20_000, 5),
    ("empty-short", _gen_empty_short, 30_000, 6),
    ("huge", _gen_huge, 80_000, 7),
]

_DIRS = {}
for label, gen, n, seed in _WRITE_SPEC:
    d = _BASE / label
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    rng = random.Random(seed)
    lines = gen(rng, n)
    with gzip.open(path, "wt", encoding="utf8") as f:
        for qid, query in lines:
            f.write(f"{qid}\t{query}\n")
    _DIRS[label] = d

# A realistic (but unused) qrel dict.  The function ignores it, but the real
# caller passes the result of load_msmarco_qrels().
_QREL = {str(1_000_000 + i): i % 2 for i in range(1000)}


def _thunk_for(directory, qrel=_QREL):
    def thunk():
        _MOD.download_dir = str(directory)
        return (qrel,)
    return thunk


# Edge-case files for checks()
_CHECK_BASE = WORKDIR / "msmarco_queries_checks"


def _make_check_file(name, lines):
    d = _CHECK_BASE / name
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    with gzip.open(path, "wt", encoding="utf8") as f:
        for line in lines:
            f.write(line + "\n")
    return d


_CHECK_DIRS = {
    "empty": _make_check_file("empty", []),
    "one": _make_check_file("one", ["1\thello world"]),
    "malformed": _make_check_file("malformed", ["this is not a tsv line"]),
}


def checks():
    return [
        ("empty-file", _thunk_for(_CHECK_DIRS["empty"])),
        ("one-line", _thunk_for(_CHECK_DIRS["one"])),
        ("malformed", _thunk_for(_CHECK_DIRS["malformed"])),
    ]


def cases():
    return [
        ("short", _thunk_for(_DIRS["short"])),
        ("medium", _thunk_for(_DIRS["medium"])),
        ("long", _thunk_for(_DIRS["long"])),
        ("punct", _thunk_for(_DIRS["punct"])),
        ("upper", _thunk_for(_DIRS["upper"])),
        ("unicode", _thunk_for(_DIRS["unicode"])),
        ("empty-short", _thunk_for(_DIRS["empty-short"])),
        ("huge", _thunk_for(_DIRS["huge"])),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['huge', 'long', 'punct', 'medium']
_KEEP_CHECKS = ['empty-file', 'one-line', 'malformed']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
