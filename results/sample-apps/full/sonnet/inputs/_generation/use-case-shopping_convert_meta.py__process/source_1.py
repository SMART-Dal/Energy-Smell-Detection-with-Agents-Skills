import random


def _word(rng, n=8):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def _text(rng, words):
    return " ".join(_word(rng, rng.randint(3, 12)) for _ in range(words))


def _make(seed, *, cats=None, cat_len=0, deep=0, rel_keys=0, rel_per_key=0,
          brand=False, title_words=6, desc_words=25):
    """Build one Amazon-meta style record, like the JSON lines convert_meta reads."""
    rng = random.Random(seed)
    data = {
        "asin": "B%09d" % rng.randrange(10 ** 9),
        "title": _text(rng, title_words),
        "description": _text(rng, desc_words),
        "price": "$%d.%02d" % (rng.randrange(1, 900), rng.randrange(100)),
        "imUrl": "http://images.example.com/%s.jpg" % _word(rng, 12),
    }
    if brand:
        data["brand"] = _word(rng, 12)
    if cats is not None:
        data["categories"] = [
            [_word(rng, 6) for _ in range(cat_len)] for _ in range(cats)
        ]
    if deep:
        # a single very deep hierarchy: stresses the "|".join(category[0:level+1]) loop
        data["categories"] = [[_word(rng, 4) for _ in range(deep)]]
    if rel_keys:
        related = {}
        for k in range(rel_keys):
            related["also_viewed_%d" % k] = [
                "B%09d" % rng.randrange(10 ** 9) for _ in range(rel_per_key)
            ]
        data["related"] = related
    return data


def _prep(data):
    # process() reads the global random module; reseed so every timed call takes
    # exactly the same path instead of consuming a shared sequence.
    random.seed(0)
    return (data,)


_DATA_MIN = _make(1)
_DATA_BRAND = _make(2, brand=True, cats=50, cat_len=3)
_DATA_SHALLOW = _make(3, cats=6000, cat_len=2)
_DATA_DEEP = _make(4, deep=1000)
_DATA_REL_ITEMS = _make(5, rel_keys=20, rel_per_key=3000)
_DATA_REL_KEYS = _make(6, rel_keys=2000, rel_per_key=5)
_DATA_MIX = _make(7, cats=1000, cat_len=6, rel_keys=100, rel_per_key=100)
_DATA_FULL = _make(8, brand=True, cats=2000, cat_len=4, rel_keys=200,
                   rel_per_key=200, title_words=200, desc_words=800)


def checks():
    return [
        ("empty-dict", lambda: _prep({})),
        ("empty-cats-related", lambda: _prep({
            "asin": "A1", "title": "t", "description": "d",
            "price": "1.00", "imUrl": "u", "categories": [], "related": {},
        })),
        ("none-values", lambda: _prep({
            "asin": None, "title": None, "description": None,
            "price": None, "imUrl": None, "brand": None,
        })),
    ]


def cases():
    return [
        ("minimal", lambda: _prep(_DATA_MIN)),
        ("brand-and-small-categories", lambda: _prep(_DATA_BRAND)),
        ("many-shallow-categories", lambda: _prep(_DATA_SHALLOW)),
        ("deep-category-chain", lambda: _prep(_DATA_DEEP)),
        ("related-many-items-per-key", lambda: _prep(_DATA_REL_ITEMS)),
        ("related-many-keys", lambda: _prep(_DATA_REL_KEYS)),
        ("categories-and-related", lambda: _prep(_DATA_MIX)),
        ("everything-large", lambda: _prep(_DATA_FULL)),
    ]
