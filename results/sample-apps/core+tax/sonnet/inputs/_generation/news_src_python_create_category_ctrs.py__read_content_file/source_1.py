import random

from create_category_ctrs import read_content_file

_CATEGORIES = [
    "news", "sports", "finance", "lifestyle", "health", "travel",
    "foodanddrink", "entertainment", "autos", "video", "music",
    "weather", "movies", "middleeast", "northamerica", "tv",
]

_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "report", "market", "team", "win", "game", "season", "player",
    "city", "government", "election", "health", "study", "research",
    "company", "stock", "price", "travel", "hotel", "food", "recipe",
    "music", "film", "actor", "weather", "storm", "rain", "snow",
    "sun", "cloud", "video", "news", "world", "local", "state",
]

_UNI = ["café", "naïve", "北京", "東京", "München", "Αθήνα", "Москва", "emoji😀", "São"]


def _text(rng, n_words, unicode_frac):
    parts = []
    for _ in range(n_words):
        if unicode_frac and rng.random() < unicode_frac:
            parts.append(rng.choice(_UNI))
        else:
            parts.append(rng.choice(_WORDS))
    return " ".join(parts)


def _write_news_file(path, n, seed, *, n_categories=16, max_words=12,
                     unicode_frac=0.0, dup_frac=0.0, empty_cat_frac=0.0):
    """Build a tab-separated news metadata file with the 8 MIND columns."""
    rng = random.Random(seed)
    cats = _CATEGORIES[:n_categories]
    out = []
    for i in range(n):
        if dup_frac and i > 0 and rng.random() < dup_frac:
            news_id = "N{}".format(rng.randrange(i))
        else:
            news_id = "N{}".format(i)
        cat = rng.choice(cats)
        sub = rng.choice(cats)
        if empty_cat_frac and rng.random() < empty_cat_frac:
            cat = ""
        title = _text(rng, max(1, int(max_words * rng.uniform(0.5, 1.5))), unicode_frac)
        abstract = _text(rng, max(1, int(max_words * 2 * rng.uniform(0.5, 1.5))), unicode_frac)
        url = "https://example.com/{}/{}".format(cat or "x", news_id)
        out.append("\t".join([news_id, cat, sub, title, abstract, url, "[]", "[]"]))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


_F_TYPICAL = WORKDIR / "news_typical.tsv"
_F_MEDIUM = WORKDIR / "news_medium.tsv"
_F_LARGE = WORKDIR / "news_large.tsv"
_F_DUP = WORKDIR / "news_dup.tsv"
_F_UNI = WORKDIR / "news_uni.tsv"
_F_LONG = WORKDIR / "news_long.tsv"
_F_EMPTY = WORKDIR / "news_empty_cat.tsv"
_F_SHORT = WORKDIR / "news_short_text.tsv"
_F_BLANK = WORKDIR / "news_blank_cat.tsv"
_F_EMPTYFILE = WORKDIR / "news_empty_file.tsv"

_write_news_file(_F_TYPICAL, 2_000, 0)
_write_news_file(_F_MEDIUM, 8_000, 1)
_write_news_file(_F_LARGE, 30_000, 2)
_write_news_file(_F_DUP, 15_000, 3, dup_frac=0.5)
_write_news_file(_F_UNI, 10_000, 4, unicode_frac=0.6)
_write_news_file(_F_LONG, 5_000, 5, max_words=80)
_write_news_file(_F_EMPTY, 12_000, 6, empty_cat_frac=0.35)
_write_news_file(_F_SHORT, 20_000, 7, max_words=3)
_write_news_file(_F_BLANK, 1, 8, empty_cat_frac=1.0)
_F_EMPTYFILE.write_text("", encoding="utf-8")


def checks():
    return [
        ("missing-file", lambda: (str(WORKDIR / "does_not_exist.tsv"), {})),
        ("empty-file", lambda: (str(_F_EMPTYFILE), {})),
        ("blank-category", lambda: (str(_F_BLANK), {})),
    ]


def cases():
    return [
        ("typical-2k", lambda: (str(_F_TYPICAL), {})),
        ("medium-8k", lambda: (str(_F_MEDIUM), {})),
        ("large-30k", lambda: (str(_F_LARGE), {})),
        ("duplicates-15k", lambda: (str(_F_DUP), {})),
        ("unicode-10k", lambda: (str(_F_UNI), {})),
        ("long-text-5k", lambda: (str(_F_LONG), {})),
        ("empty-cat-12k", lambda: (str(_F_EMPTY), {})),
        ("short-text-20k", lambda: (str(_F_SHORT), {})),
    ]
