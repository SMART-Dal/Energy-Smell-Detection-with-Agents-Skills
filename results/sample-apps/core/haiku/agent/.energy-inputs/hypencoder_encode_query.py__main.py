# Inputs for hypencoder/encode_query.py::main, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
import sys

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

_LARGE_VOCAB = 60000
_SMALL_VOCAB = 5000

_TOKENIZER_LARGE = WORKDIR / "tokenizer_large.json"
_TOKENIZER_SMALL = WORKDIR / "tokenizer_small.json"


def _build_tokenizer(path, vocab_size):
    # A real tokenizer.json, built with the same library the function uses.
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i in range(vocab_size):
        vocab[f"tok{i}"] = len(vocab)
    tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    tok.save(str(path))


_build_tokenizer(_TOKENIZER_LARGE, _LARGE_VOCAB)
_build_tokenizer(_TOKENIZER_SMALL, _SMALL_VOCAB)


def _query(n_words, seed, unknown_ratio=0.0):
    rng = random.Random(seed)
    words = []
    for _ in range(n_words):
        if rng.random() < unknown_ratio:
            words.append("zz%d" % rng.randrange(10 ** 9))
        else:
            words.append("tok%d" % rng.randrange(_LARGE_VOCAB))
    return " ".join(words)


def _setup(argv):
    # main() reads sys.argv via argparse; this is setup, not the timed call.
    sys.argv = list(argv)
    return ()


def _argv(query, tokenizer, extra=()):
    return ["encode_query.py", query, "--tokenizer", str(tokenizer)] + list(extra)


def checks():
    return [
        ("empty-query", lambda: _setup(_argv("", _TOKENIZER_SMALL))),
        ("single-token", lambda: _setup(_argv("tok0", _TOKENIZER_SMALL))),
        ("cosine-empty", lambda: _setup(_argv("", _TOKENIZER_SMALL, ["--cosine"]))),
    ]


def cases():
    q_short = _query(40, 1)
    q_med = _query(800, 2)
    q_long = _query(20000, 3)
    q_huge = _query(30000, 4)
    q_mixed = _query(3000, 5, unknown_ratio=0.4)

    return [
        ("default-short-large", lambda: _setup(_argv(q_short, _TOKENIZER_LARGE))),
        ("default-long-large", lambda: _setup(_argv(q_long, _TOKENIZER_LARGE))),
        ("default-huge-small", lambda: _setup(_argv(q_huge, _TOKENIZER_SMALL))),
        ("default-mixed-hits100",
         lambda: _setup(_argv(q_mixed, _TOKENIZER_LARGE, ["--hits", "100"]))),
        ("rerank-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--rerank"]))),
        ("rerank-long-small", lambda: _setup(_argv(q_long, _TOKENIZER_SMALL, ["--rerank"]))),
        ("lexical-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--lexical"]))),
        ("cosine-long", lambda: _setup(_argv(q_long, _TOKENIZER_LARGE, ["--cosine"]))),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['default-long-large', 'default-huge-small', 'default-mixed-hits100', 'rerank-medium']
_KEEP_CHECKS = ['empty-query', 'single-token', 'cosine-empty']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
