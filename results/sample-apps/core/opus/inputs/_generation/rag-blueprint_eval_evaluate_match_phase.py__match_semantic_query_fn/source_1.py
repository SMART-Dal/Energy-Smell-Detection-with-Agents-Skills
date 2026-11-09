import random

# ---------------------------------------------------------------------------
# Input data for match_semantic_query_fn(query_text: str, top_k: int).
# The function only builds a YQL string from the query text, so the workload is
# driven by the size / shape of the query text (and, nominally, top_k).
# All data is built once at module level and the thunks only return it.
# ---------------------------------------------------------------------------

_WORDS = [
    "retrieval", "augmented", "generation", "vector", "embedding", "semantic",
    "search", "ranking", "nearest", "neighbor", "document", "chunk", "context",
    "model", "inference", "similarity", "distance", "cosine", "index", "corpus",
    "query", "answer", "passage", "token", "encoder", "transformer", "prompt",
    "evaluation", "phase", "match", "hybrid", "weakand", "vespa", "schema",
    "blueprint", "sample", "application", "language", "natural", "processing",
    "knowledge", "base", "question", "response", "pipeline", "latency", "score",
]

_UNICODE_WORDS = [
    "検索", "意味", "埋め込み", "文書", "回答", "質問", "評価", "類似",
    "récupération", "informations", "modèle", "requête", "réponse", "évaluation",
    "поиск", "вектор", "документ", "запрос", "ответ", "оценка",
    "بحث", "متجه", "مستند", "استعلام", "إجابة", "تقييم",
]


def _make_text(n_words, seed, vocab=_WORDS):
    rng = random.Random(seed)
    return " ".join(rng.choice(vocab) for _ in range(n_words))


def _make_special_text(n_words, seed):
    rng = random.Random(seed)
    pieces = []
    for _ in range(n_words):
        w = rng.choice(_WORDS)
        # quotes, backslashes, operators, punctuation that must survive quoting
        flavour = rng.randrange(6)
        if flavour == 0:
            pieces.append(f'"{w}"')
        elif flavour == 1:
            pieces.append(f"{w}'s")
        elif flavour == 2:
            pieces.append(f"({w} OR {w.upper()})")
        elif flavour == 3:
            pieces.append(f"{w}\\{w}")
        elif flavour == 4:
            pieces.append(f"{w}, {w}; {w}:")
        else:
            pieces.append(f"NOT {w}")
    return " ".join(pieces)


def _make_sentence_text(n_sentences, seed):
    rng = random.Random(seed)
    sentences = []
    for _ in range(n_sentences):
        length = rng.randint(6, 18)
        words = [rng.choice(_WORDS) for _ in range(length)]
        sentences.append(" ".join(words).capitalize() + ".")
    return " ".join(sentences)


def _make_numeric_text(n_tokens, seed):
    rng = random.Random(seed)
    return " ".join(
        f"{rng.choice(_WORDS)}{rng.randint(0, 10 ** 9)}" for _ in range(n_tokens)
    )


# Pre-built query texts (module level: never timed).
_T_SHORT = "what is retrieval augmented generation"
_T_MEDIUM = _make_text(60, 0)
_T_LONG = _make_text(400, 1)
_T_VERY_LONG = _make_text(4000, 2)
_T_SENTENCES = _make_sentence_text(120, 3)
_T_SPECIAL = _make_special_text(300, 4)
_T_UNICODE = " ".join(
    random.Random(5).choice(_UNICODE_WORDS) for _ in range(250)
)
_T_NUMERIC = _make_numeric_text(500, 6)


def checks():
    return [
        ("empty-query", lambda: ("", 10)),
        ("single-char", lambda: ("?", 1)),
        ("none-query", lambda: (None, 10)),
    ]


def cases():
    return [
        ("short-query", lambda: (_T_SHORT, 10)),
        ("medium-query-top1", lambda: (_T_MEDIUM, 1)),
        ("long-query-top100", lambda: (_T_LONG, 100)),
        ("very-long-query", lambda: (_T_VERY_LONG, 20)),
        ("multi-sentence-query", lambda: (_T_SENTENCES, 50)),
        ("special-chars-query", lambda: (_T_SPECIAL, 10)),
        ("unicode-query", lambda: (_T_UNICODE, 5)),
        ("numeric-query-top1000", lambda: (_T_NUMERIC, 1000)),
    ]
