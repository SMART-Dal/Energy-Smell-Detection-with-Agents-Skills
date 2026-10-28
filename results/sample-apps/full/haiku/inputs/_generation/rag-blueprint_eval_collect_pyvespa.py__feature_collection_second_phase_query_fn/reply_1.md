```python
import random

from collect_pyvespa import feature_collection_second_phase_query_fn


def _random_text(n_words, seed, alphabet=None):
    rng = random.Random(seed)
    if alphabet is None:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
    words = []
    for _ in range(n_words):
        wlen = rng.randint(2, 12)
        words.append("".join(rng.choice(alphabet) for _ in range(wlen)))
    return " ".join(words)


def _chars_text(length, seed):
    rng = random.Random(seed)
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?-()[]{}'\"\n\t/\\@#$%&*+=<>|~^`"
    return "".join(rng.choice(chars) for _ in range(length))


# Module-level precomputed query texts (built once, reused by the thunks).
_LONG_SENTENCE_QUERY = (
    "What are the main differences between the transformer architecture and "
    "recurrent neural networks for long sequence modelling, and how do "
    "attention mechanisms address the vanishing gradient problem in practice? "
    "Please compare training cost, memory usage, and parallelisation behaviour "
    "across both families of models in detail."
)

_MULTILINGUAL_QUERY = (
    "Künstliche Intelligenz und maschinelles Lernen – 機械学習の応用、"
    "そしてデータサイエンスの未来について教えてください。"
)

_NUMERIC_QUERY = " ".join(
    f"item{i}-{i * 37 % 997}" for i in range(120)
)

_CHARS_QUERY = _chars_text(4000, 7)

_LONG_WORDS_QUERY = _random_text(4000, 11)

_SHORT_QUERY = "vespa ranking features"

_REPEATED_QUERY = " ".join(["retrieval augmented generation"] * 60)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("empty-topk-zero", lambda: ("hello world", 0)),
        ("none-query-id", lambda: call("test query", top_k=5, query_id=None)),
    ]


def cases():
    return [
        ("short-default", lambda: (_SHORT_QUERY,)),
        ("long-sentence-top50", lambda: call(_LONG_SENTENCE_QUERY, top_k=50)),
        ("multilingual-top1", lambda: call(_MULTILINGUAL_QUERY, top_k=1)),
        ("numeric-top100", lambda: call(_NUMERIC_QUERY, top_k=100)),
        ("chars-4000-top10", lambda: call(_CHARS_QUERY, top_k=10)),
        ("long-words-top500", lambda: call(_LONG_WORDS_QUERY, top_k=500)),
        ("repeated-top1000", lambda: call(_REPEATED_QUERY, top_k=1000, query_id="q-42")),
        ("with-query-id-top25", lambda: call(_LONG_SENTENCE_QUERY, top_k=25, query_id="session-7-query-3")),
    ]
```