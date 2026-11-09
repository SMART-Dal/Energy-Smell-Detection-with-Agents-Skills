# Inputs for news/src/python/mind_data.py::MindData.sample_valid_data, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

from mind_data import MindData


def _make_news(n, seed):
    rng = random.Random(seed)
    return {
        i: {
            "category_index": rng.randrange(50),
            "subcategory_index": rng.randrange(200),
            "entity_index": rng.randrange(1000),
        }
        for i in range(n)
    }


def _make_impressions(count, news_count, min_len, max_len, seed, label_mode="mixed", user_start=0):
    rng = random.Random(seed)
    impressions = []
    for i in range(count):
        length = rng.randint(min_len, max_len)
        news_indices = [rng.randrange(news_count) for _ in range(length)]

        if label_mode == "mixed":
            labels = [rng.randint(0, 1) for _ in range(length)]
            if all(label == 0 for label in labels):
                labels[0] = 1
            if all(label == 1 for label in labels):
                labels[0] = 0
        elif label_mode == "all_one":
            labels = [1] * length
        elif label_mode == "all_zero":
            labels = [0] * length
        elif label_mode == "mostly_clicked":
            labels = [1] * length
            if length > 1:
                labels[rng.randrange(length)] = 0
        else:
            raise ValueError(label_mode)

        impressions.append(
            {
                "news_indices": news_indices,
                "labels": labels,
                "user_index": user_start + i,
            }
        )
    return impressions


def _instance(valid_impressions, train_impressions, news_content):
    instance = MindData.__new__(MindData)
    instance.news_content = news_content
    instance.valid_impressions = valid_impressions
    instance.train_impressions = train_impressions
    return instance


def _mk(instance, prob=1.0, train=False, seed=0):
    random.seed(seed)
    return (instance, prob, train)


# Case A: typical valid impressions, moderate news list length.
_NEWS_A = _make_news(5000, 1)
_VALID_A = _make_impressions(800, 5000, 10, 30, 2, "mixed")
_INST_A = _instance(_VALID_A, [], _NEWS_A)

# Case B: fewer impressions, but long news lists.
_NEWS_B = _make_news(5000, 3)
_VALID_B = _make_impressions(200, 5000, 50, 100, 4, "mixed")
_INST_B = _instance(_VALID_B, [], _NEWS_B)

# Case C: many impressions, short lists, partial sampling.
_NEWS_C = _make_news(5000, 5)
_VALID_C = _make_impressions(2000, 5000, 5, 15, 6, "mixed")
_INST_C = _instance(_VALID_C, [], _NEWS_C)

# Case D: medium lists, high sampling probability.
_NEWS_D = _make_news(5000, 7)
_VALID_D = _make_impressions(500, 5000, 20, 40, 8, "mixed")
_INST_D = _instance(_VALID_D, [], _NEWS_D)

# Case E: train impressions are used instead of valid impressions.
_NEWS_E = _make_news(5000, 9)
_VALID_E = _make_impressions(20, 5000, 5, 10, 10, "mixed")
_TRAIN_E = _make_impressions(800, 5000, 10, 25, 11, "mixed")
_INST_E = _instance(_VALID_E, _TRAIN_E, _NEWS_E)

# Case F: labels are all one, so every impression takes the skip path.
_NEWS_F = _make_news(5000, 12)
_VALID_F = _make_impressions(800, 5000, 10, 30, 13, "all_one")
_INST_F = _instance(_VALID_F, [], _NEWS_F)

# Case G: a few impressions with very long news lists.
_NEWS_G = _make_news(5000, 14)
_VALID_G = _make_impressions(50, 5000, 200, 400, 15, "mixed")
_INST_G = _instance(_VALID_G, [], _NEWS_G)

# Case H: many short impressions with low sampling probability.
_NEWS_H = _make_news(5000, 16)
_VALID_H = _make_impressions(5000, 5000, 2, 6, 17, "mixed")
_INST_H = _instance(_VALID_H, [], _NEWS_H)


def checks():
    empty_news = {}
    empty_instance = _instance([], [], empty_news)

    single_news = {
        0: {"category_index": 0, "subcategory_index": 0, "entity_index": 0},
        1: {"category_index": 1, "subcategory_index": 1, "entity_index": 1},
    }
    single_mixed_instance = _instance(
        [{"news_indices": [0, 1], "labels": [1, 0], "user_index": 0}],
        [],
        single_news,
    )
    single_all_one_instance = _instance(
        [{"news_indices": [0, 1], "labels": [1, 1], "user_index": 0}],
        [],
        single_news,
    )

    return [
        ("empty", lambda: _mk(empty_instance, 1.0, False, 0)),
        ("single-mixed", lambda: _mk(single_mixed_instance, 1.0, False, 0)),
        ("single-all-one", lambda: _mk(single_all_one_instance, 1.0, False, 0)),
    ]


def cases():
    return [
        ("typical-valid", lambda: _mk(_INST_A, 1.0, False, 100)),
        ("long-news-lists", lambda: _mk(_INST_B, 1.0, False, 101)),
        ("many-short-partial", lambda: _mk(_INST_C, 0.5, False, 102)),
        ("medium-high-prob", lambda: _mk(_INST_D, 0.9, False, 103)),
        ("train-impressions", lambda: _mk(_INST_E, 1.0, True, 104)),
        ("all-one-labels", lambda: _mk(_INST_F, 1.0, False, 105)),
        ("few-very-long", lambda: _mk(_INST_G, 1.0, False, 106)),
        ("many-short-low-prob", lambda: _mk(_INST_H, 0.3, False, 107)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-short-low-prob', 'many-short-partial', 'typical-valid', 'train-impressions']
_KEEP_CHECKS = ['empty', 'single-mixed', 'single-all-one']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
