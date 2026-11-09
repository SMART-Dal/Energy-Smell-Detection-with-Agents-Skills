# Inputs for news/src/python/mind_data.py::MindData.add_impressions, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
from mind_data import MindData

# Build a shared news_content table large enough for every case.
_MAX_INDEX = 100_200
_rng = random.Random(0)
_NEWS_CONTENT = {}
for _i in range(_MAX_INDEX):
    _NEWS_CONTENT[_i] = {
        "category_index": _rng.randrange(100),
        "subcategory_index": _rng.randrange(1_000),
        "entity_index": _rng.randrange(10_000),
    }

# Create a MindData instance without going through __init__ (which would read files).
# We only need the fields that add_impressions / find_clicked use.
_instance = object.__new__(MindData)
_instance.news_content = _NEWS_CONTENT
_instance.user_map = {}
_instance.news_map = {}
_instance.cat_map = {}
_instance.sub_cat_map = {}
_instance.entity_map = {}
_instance.train_impressions = []
_instance.valid_impressions = []


def _make_impression(num_positive, num_negative):
    """Build an impression with the requested number of positive/negative news items."""
    news_indices = list(range(num_positive)) + list(range(num_positive, num_positive + num_negative))
    labels = [1] * num_positive + [0] * num_negative
    return {
        "user_index": 0,
        "news_indices": news_indices,
        "labels": labels,
    }


def _make_thunk(impression, num_negatives, seed):
    """Return a thunk that seeds random and supplies fresh output lists."""
    def thunk():
        random.seed(seed)
        return (
            _instance,
            impression,
            [],  # user_indices
            [],  # news_indices
            [],  # category_indices
            [],  # subcategory_indices
            [],  # entity_indices
            [],  # labels
            num_negatives,
        )
    return thunk


def checks():
    empty_imp = {"user_index": 0, "news_indices": [], "labels": []}
    one_pos_one_neg = _make_impression(1, 1)
    zero_neg = _make_impression(1, 5)
    return [
        ("empty", _make_thunk(empty_imp, 4, 0)),
        ("one-positive-one-negative", _make_thunk(one_pos_one_neg, 1, 1)),
        ("num-negatives-zero", _make_thunk(zero_neg, 0, 2)),
    ]


def cases():
    return [
        ("typical", _make_thunk(_make_impression(1_000, 5_000), 10, 1)),
        ("large-positives", _make_thunk(_make_impression(5_000, 5_000), 4, 2)),
        ("many-negatives", _make_thunk(_make_impression(500, 20_000), 50, 3)),
        ("k-greater-than-negatives", _make_thunk(_make_impression(2_000, 3), 10, 4)),
        ("single-positive-many-negatives", _make_thunk(_make_impression(1, 50_000), 100, 5)),
        ("many-positives-few-negatives", _make_thunk(_make_impression(10_000, 1_000), 1, 6)),
        ("heavy-sampling", _make_thunk(_make_impression(200, 100_000), 200, 7)),
        ("medium", _make_thunk(_make_impression(2_000, 5_000), 20, 8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['heavy-sampling', 'medium', 'many-positives-few-negatives', 'large-positives']
_KEEP_CHECKS = ['empty', 'one-positive-one-negative', 'num-negatives-zero']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
