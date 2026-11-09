```python
import random
from collections import defaultdict

from create_category_ctrs import read_impressions_file

# ---------------------------------------------------------------------------
# Shared, module-level data (built once, never timed).
# ---------------------------------------------------------------------------

_CATEGORIES = [
    "news", "sports", "finance", "foodanddrink", "lifestyle", "travel",
    "video", "music", "weather", "autos", "health", "entertainment",
    "tv", "movies", "kids", "northamerica", "middleeast", "europe",
    "asia", "africa",
]


def _build_news_map(n_ids, seed):
    rng = random.Random(seed)
    return {
        "N{}".format(i): _CATEGORIES[rng.randrange(len(_CATEGORIES))]
        for i in range(n_ids)
    }


_NEWS_MAP = _build_news_map(5000, 12345)
_ALL_NEWS_IDS = list(_NEWS_MAP.keys())
_SKEW_NEWS_IDS = _ALL_NEWS_IDS[:40]          # concentrated in a few categories


def _new_click_map():
    # main() builds a fresh defaultdict for every impressions file
    return defaultdict(lambda: {"clicks": 0, "impressions": 0})


def _write_impressions(path, n_lines, imps_per_line, news_ids, hit_ratio,
                       click_ratio, seed, history_len=3):
    """Write a tab separated impressions file in the repository's format."""
    rng = random.Random(seed)
    n_ids = len(news_ids)
    lines = []
    for i in range(n_lines):
        imps = []
        for _ in range(imps_per_line):
            if rng.random() < hit_ratio:
                nid = news_ids[rng.randrange(n_ids)]
            else:
                nid = "M{}".format(rng.randrange(10 ** 9))
            imps.append(nid + ("-1" if rng.random() < click_ratio else "-0"))
        hist = " ".join(news_ids[rng.randrange(n_ids)] for _ in range(history_len))
        lines.append("\t".join((
            "I{}".format(i),
            "U{}".format(rng.randrange(100000)),
            str(1500000000 + rng.randrange(10 ** 7)),
            hist,
            " ".join(imps),
        )))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Measured workloads: 8 distinct impressions files.
# ---------------------------------------------------------------------------

_FILE_TYPICAL = _write_impressions(
    WORKDIR / "imp_typical.tsv", 3000, 15, _ALL_NEWS_IDS, 0.90, 0.40, 1)

_FILE_LARGE = _write_impressions(
    WORKDIR / "imp_large.tsv", 6000, 15, _ALL_NEWS_IDS, 0.85, 0.30, 2)

_FILE_MISSES = _write_impressions(
    WORKDIR / "imp_misses.tsv", 4000, 15, _ALL_NEWS_IDS, 0.08, 0.50, 3)

_FILE_ALLHITS = _write_impressions(
    WORKDIR / "imp_allhits.tsv", 4000, 10, _ALL_NEWS_IDS, 1.00, 0.90, 4)

_FILE_LONG = _write_impressions(
    WORKDIR / "imp_long.tsv", 600, 80, _ALL_NEWS_IDS, 0.75, 0.35, 5)

_FILE_SINGLE = _write_impressions(
    WORKDIR / "imp_single.tsv", 40000, 1, _ALL_NEWS_IDS, 0.90, 0.50, 6)

_FILE_SKEW = _write_impressions(
    WORKDIR / "imp_skew.tsv", 5000, 20, _SKEW_NEWS_IDS, 0.95, 0.50, 7)

_FILE_DIVERSE = _write_impressions(
    WORKDIR / "imp_diverse.tsv", 5000, 12, _ALL_NEWS_IDS, 0.50, 0.60, 8)


# ---------------------------------------------------------------------------
# Edge inputs (only checked, never measured).
# ---------------------------------------------------------------------------

_CHECK_EMPTY = WORKDIR / "imp_empty.tsv"
_CHECK_EMPTY.write_text("", encoding="utf-8")

_CHECK_HIT = WORKDIR / "imp_one_hit.tsv"
_CHECK_HIT.write_text("I0\tU0\t1500000000\tN1 N2\tN1-1 N2-0\n", encoding="utf-8")

_CHECK_MISS = WORKDIR / "imp_one_miss.tsv"
_CHECK_MISS.write_text("I0\tU0\t1500000000\tN1\tM999-1\n", encoding="utf-8")


def checks():
    return [
        ("empty-file", lambda: (str(_CHECK_EMPTY), _new_click_map(), _NEWS_MAP)),
        ("single-hit", lambda: (str(_CHECK_HIT), _new_click_map(), _NEWS_MAP)),
        ("single-miss", lambda: (str(_CHECK_MISS), _new_click_map(), _NEWS_MAP)),
    ]


def cases():
    return [
        ("typical", lambda: (_FILE_TYPICAL, _new_click_map(), _NEWS_MAP)),
        ("large", lambda: (_FILE_LARGE, _new_click_map(), _NEWS_MAP)),
        ("mostly-misses", lambda: (_FILE_MISSES, _new_click_map(), _NEWS_MAP)),
        ("all-hits-high-click", lambda: (_FILE_ALLHITS, _new_click_map(), _NEWS_MAP)),
        ("long-impressions", lambda: (_FILE_LONG, _new_click_map(), _NEWS_MAP)),
        ("single-impression", lambda: (_FILE_SINGLE, _new_click_map(), _NEWS_MAP)),
        ("skewed-categories", lambda: (_FILE_SKEW, _new_click_map(), _NEWS_MAP)),
        ("diverse", lambda: (_FILE_DIVERSE, _new_click_map(), _NEWS_MAP)),
    ]
```