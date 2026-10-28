import io
import random

import numpy as np
import torch

from train_cold_start import read_bert_embeddings


EMB_DIM = 512
# 190 * 512 = 97280 returned values, under the 100k output budget.
NUM_NEWS = 190
NEWS_IDS = ["N%d" % i for i in range(NUM_NEWS)]
NEWS_MAP = {nid: i for i, nid in enumerate(NEWS_IDS)}


class _DataLoader:
    """Holds the news-id -> index map that read_bert_embeddings reads via .news()."""

    def __init__(self, news_map):
        self._news = news_map

    def news(self):
        return self._news


def _emb_line(nid, rng):
    return nid + "\t" + ",".join("%.6f" % rng.uniform(-1.0, 1.0) for _ in range(EMB_DIM))


def _extra_line(rng, kind):
    if kind == "short":
        return "X%d\n" % rng.randrange(10 ** 9)
    if kind == "tabbed":
        return "X%d\t%s\n" % (
            rng.randrange(10 ** 9),
            "".join(rng.choice("abcdefghij") for _ in range(24)),
        )
    # long: a big second field, so the tab split itself costs something
    return "X%d\t%s\n" % (
        rng.randrange(10 ** 9),
        ",".join(str(rng.randrange(10)) for _ in range(64)),
    )


def _build_file(path, hit_ids, extra_lines, seed, kind="short"):
    """Write a BERT-embeddings TSV: matched news rows plus many unmatched rows."""
    rng = random.Random(seed)
    chunks = []
    for nid in hit_ids:
        chunks.append(_emb_line(nid, rng))
        chunks.append("\n")
    for _ in range(extra_lines):
        chunks.append(_extra_line(rng, kind))
    with io.open(str(path), "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return str(path)


def _case(name, train_hits, train_extra, valid_hits, valid_extra, seed, kind="short"):
    train_path = _build_file(WORKDIR / (name + "_train.tsv"), train_hits, train_extra, seed, kind)
    valid_path = _build_file(WORKDIR / (name + "_valid.tsv"), valid_hits, valid_extra, seed + 7919, kind)
    loader = _DataLoader(NEWS_MAP)
    return (name, lambda: (loader, train_path, valid_path))


_ALL = list(NEWS_IDS)
_EVEN = _ALL[0::2]
_ODD = _ALL[1::2]
_FIRST50 = _ALL[:50]
_NEXT50 = _ALL[50:100]

_CASES = [
    # train fills every row, valid contributes nothing but scanning work
    _case("c1_train_full", _ALL, 80_000, [], 40_000, 101, "short"),
    # train matches nothing, valid fills every row
    _case("c2_valid_full", [], 30_000, _ALL, 80_000, 202, "short"),
    # disjoint halves: every row filled, from two different files
    _case("c3_split", _EVEN, 60_000, _ODD, 60_000, 303, "tabbed"),
    # both files fill every row, valid overwrites train
    _case("c4_overlap", _ALL, 50_000, _ALL, 50_000, 404, "short"),
    # the big one: 300k scanned lines
    _case("c5_large", _ALL, 150_000, [], 150_000, 505, "short"),
    # heavy tab-splitting on long unmatched lines
    _case("c6_longlines", _ALL, 60_000, [], 60_000, 606, "long"),
    # partial coverage: half the rows stay zero
    _case("c7_partial", _FIRST50, 100_000, _NEXT50, 100_000, 707, "tabbed"),
    # very sparse hits among a lot of unmatched lines
    _case("c8_sparse", _ALL[:10], 130_000, _ALL[10:20], 130_000, 808, "short"),
]


def cases():
    return _CASES


def checks():
    empty_train = WORKDIR / "check_empty_train.tsv"
    empty_valid = WORKDIR / "check_empty_valid.tsv"
    empty_train.write_text("", encoding="utf-8")
    empty_valid.write_text("", encoding="utf-8")

    nomatch_train = WORKDIR / "check_nomatch_train.tsv"
    nomatch_train.write_text("X1\nX2\n", encoding="utf-8")

    missing = WORKDIR / "check_missing.tsv"
    if missing.exists():
        missing.unlink()

    return [
        ("empty-news", lambda: (_DataLoader({}), str(empty_train), str(empty_valid))),
        ("single-news-no-match", lambda: (_DataLoader({"N0": 0}), str(nomatch_train), str(empty_valid))),
        ("missing-file", lambda: (_DataLoader(NEWS_MAP), str(missing), str(empty_valid))),
    ]
