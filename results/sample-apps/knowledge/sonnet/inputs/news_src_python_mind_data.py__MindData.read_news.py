# Inputs for news/src/python/mind_data.py::MindData.read_news, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import json
import random

from mind_data import MindData

# ---------------------------------------------------------------------------
# Realistic MIND-style vocabulary (news.tsv categories / subcategories)
# ---------------------------------------------------------------------------
_CATEGORIES = [
    "news", "sports", "finance", "lifestyle", "health", "travel",
    "autos", "entertainment", "foodanddrink", "movies", "music",
    "weather", "video", "kids",
]
_SUBCATS = [
    "newscategory", "football", "nfl", "basketball", "mlb", "nba",
    "soccer", "golf", "tennis", "movies", "tv", "music",
    "celebrities", "health", "medical", "travel", "food", "recipes",
    "autos", "weather",
]

# ---------------------------------------------------------------------------
# The MindData instance is built the way the repository's own callers do
# (MindData(...)), using small real files so the constructor runs its normal
# read_data / read_news path.  Those files are empty, so the constructor only
# initialises the maps; the measured read_news call does all the work.
# ---------------------------------------------------------------------------
_EMPTY_IMPR = WORKDIR / "empty_impressions.tsv"
_EMPTY_NEWS = WORKDIR / "empty_news.tsv"
_EMPTY_IMPR.write_text("", encoding="utf-8")
_EMPTY_NEWS.write_text("", encoding="utf-8")


def _new_mind():
    return MindData(str(_EMPTY_NEWS), str(_EMPTY_IMPR),
                    str(_EMPTY_NEWS), str(_EMPTY_IMPR))


# ---------------------------------------------------------------------------
# News-file generation
# ---------------------------------------------------------------------------
def _entities_json(rng, count, pool):
    ents = []
    for _ in range(count):
        qid = pool[rng.randrange(len(pool))]
        ents.append({
            "Label": "entity_" + qid,
            "Type": rng.choice(["P", "O", "T"]),
            "WikidataId": qid,
            "Confidence": round(rng.uniform(0.5, 1.0), 3),
            "SurfaceForms": ["surface_" + str(rng.randrange(50))],
        })
    return json.dumps(ents)


def _gen(path, n, seed, mode="both", ent_lo=1, ent_hi=3, text_len=8,
         n_doc=0, n_cat=0, n_sub=0, ent_pool_size=500):
    """Write a tab separated news file.

    mode: "none"  -> 6 fields (no entity columns)
          "title" -> 7 fields (title entities only)
          "both"  -> 8 fields (title + abstract entities)
          "mixed" -> random mix of the three shapes
    n_doc/n_cat/n_sub == 0 -> unique value per line, otherwise drawn from a
    pool of that many distinct values (duplicates).
    """
    rng = random.Random(seed)
    pool = ["Q" + str(i) for i in range(ent_pool_size)]
    lines = []
    for i in range(n):
        if n_doc == 0:
            doc_id = "N" + str(100000 + i)
        else:
            doc_id = "N" + str(100000 + rng.randrange(n_doc))
        if n_cat == 0:
            category = _CATEGORIES[rng.randrange(len(_CATEGORIES))]
        else:
            category = "cat" + str(rng.randrange(n_cat))
        if n_sub == 0:
            subcategory = _SUBCATS[rng.randrange(len(_SUBCATS))]
        else:
            subcategory = "sub" + str(rng.randrange(n_sub))

        title = " ".join("t" + str(rng.randrange(1000)) for _ in range(text_len))
        abstract = " ".join("a" + str(rng.randrange(1000)) for _ in range(text_len))
        url = "http://example.com/news/" + str(i)
        base = [doc_id, category, subcategory, title, abstract, url]

        if mode == "none":
            lines.append("\t".join(base))
        elif mode == "title":
            lines.append("\t".join(
                base + [_entities_json(rng, rng.randint(ent_lo, ent_hi), pool)]))
        elif mode == "mixed":
            r = rng.random()
            if r < 0.34:
                lines.append("\t".join(base))
            elif r < 0.67:
                lines.append("\t".join(
                    base + [_entities_json(rng, rng.randint(ent_lo, ent_hi), pool)]))
            else:
                lines.append("\t".join(base + [
                    _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                    _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                ]))
        else:  # "both"
            lines.append("\t".join(base + [
                _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
            ]))

    text = "\n".join(lines)
    if lines:
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Measured workloads (built once, at import time)
# ---------------------------------------------------------------------------
_F = {
    "noent":    _gen(WORKDIR / "news_noent.tsv", 2000, 0, mode="none", text_len=8),
    "fewent":   _gen(WORKDIR / "news_fewent.tsv", 5000, 1, mode="both",
                     ent_lo=1, ent_hi=3, text_len=10),
    "manyent":  _gen(WORKDIR / "news_manyent.tsv", 2500, 2, mode="both",
                     ent_lo=6, ent_hi=15, text_len=8),
    "mixed":    _gen(WORKDIR / "news_mixed.tsv", 8000, 3, mode="mixed",
                     ent_lo=0, ent_hi=4, text_len=10),
    "dups":     _gen(WORKDIR / "news_dups.tsv", 6000, 4, mode="both",
                     ent_lo=1, ent_hi=3, text_len=10,
                     n_doc=200, n_cat=5, n_sub=8),
    "distinct": _gen(WORKDIR / "news_distinct.tsv", 7000, 5, mode="both",
                     ent_lo=1, ent_hi=3, text_len=10,
                     n_cat=5000, n_sub=6000, ent_pool_size=4000),
    "long":     _gen(WORKDIR / "news_long.tsv", 4000, 6, mode="both",
                     ent_lo=1, ent_hi=2, text_len=60),
    "large":    _gen(WORKDIR / "news_large.tsv", 10000, 7, mode="mixed",
                     ent_lo=0, ent_hi=5, text_len=10),
}

# ---------------------------------------------------------------------------
# Edge inputs (never measured)
# ---------------------------------------------------------------------------
_C = {
    "empty": _gen(WORKDIR / "news_empty.tsv", 0, 100, mode="none"),
    "one6":  _gen(WORKDIR / "news_one6.tsv", 1, 101, mode="none", text_len=5),
    "one8":  _gen(WORKDIR / "news_one8.tsv", 1, 102, mode="both",
                  ent_lo=2, ent_hi=2, text_len=5),
}


def _mk(path):
    # A fresh instance per thunk call: read_news mutates self.news_content and
    # the lookup maps, so a new instance keeps every call on the same path.
    return lambda: (_new_mind(), str(path))


def checks():
    return [
        ("empty-file", _mk(_C["empty"])),
        ("single-line-6-fields", _mk(_C["one6"])),
        ("single-line-8-fields", _mk(_C["one8"])),
    ]


def cases():
    return [
        ("no-entities", _mk(_F["noent"])),
        ("few-entities", _mk(_F["fewent"])),
        ("many-entities", _mk(_F["manyent"])),
        ("mixed-field-counts", _mk(_F["mixed"])),
        ("duplicate-ids", _mk(_F["dups"])),
        ("all-distinct-keys", _mk(_F["distinct"])),
        ("long-text", _mk(_F["long"])),
        ("large-mixed", _mk(_F["large"])),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['all-distinct-keys', 'large-mixed', 'many-entities', 'few-entities']
_KEEP_CHECKS = ['empty-file', 'single-line-6-fields', 'single-line-8-fields']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
