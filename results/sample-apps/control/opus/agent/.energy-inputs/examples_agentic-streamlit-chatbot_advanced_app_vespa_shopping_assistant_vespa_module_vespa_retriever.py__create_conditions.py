# Inputs for examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from vespa_shopping_assistant.vespa_module.vespa_retriever import create_conditions

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------
_NUM_FIELDS = [
    "price", "rating", "stock_count", "weight", "discount",
    "size", "year", "quantity", "popularity", "review_count",
]
_TEXT_FIELDS = [
    "brand", "category", "color", "description", "title",
    "material", "tags", "seller",
]
_WORDS = [
    "Nike", "Adidas", "Puma", "Reebok", "Red", "Blue", "Green", "Black",
    "Running", "Shoes", "Cotton", "Leather", "Summer", "Winter", "Pro",
    "Max", "Air", "Ultra", "Classic", "Sport", "Casual", "Slim", "Large",
    "Small", "Waterproof", "Lightweight",
]
_NUM_OPS = [">", "<", "=", "!=", ">=", "<="]


# ---------------------------------------------------------------------------
# Generators (run once, at module level)
# ---------------------------------------------------------------------------
def _numeric(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        f = rng.choice(_NUM_FIELDS)
        op = rng.choice(_NUM_OPS)
        if rng.random() < 0.5:
            v = str(rng.randint(0, 1_000_000))
        else:
            v = f"{rng.uniform(0.0, 5000.0):.{rng.randint(1, 4)}f}"
        out.append(f"{f} {op} {v}")
    return out


def _contains(n, seed, max_words=3):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        f = rng.choice(_TEXT_FIELDS)
        k = rng.randint(1, max_words)
        v = " ".join(rng.choice(_WORDS) for _ in range(k))
        out.append(f"{f} contains {v}")
    return out


def _mixed(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if rng.random() < 0.4:
            f = rng.choice(_TEXT_FIELDS)
            k = rng.randint(1, 3)
            v = " ".join(rng.choice(_WORDS) for _ in range(k))
            out.append(f"{f} contains {v}")
        else:
            f = rng.choice(_NUM_FIELDS)
            op = rng.choice(_NUM_OPS)
            if rng.random() < 0.5:
                v = str(rng.randint(0, 500))
            else:
                v = f"{rng.uniform(0.0, 999.0):.3f}"
            out.append(f"{f} {op} {v}")
    return out


def _string_eq(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        f = rng.choice(_TEXT_FIELDS)
        op = rng.choice(["=", "!="])
        v = rng.choice(_WORDS)
        out.append(f"{f} {op} {v}")
    return out


def _long_values(n, seed):
    """Values that carry embedded spaces (exercise the maxsplit=3 split)."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if rng.random() < 0.5:
            f = rng.choice(_TEXT_FIELDS)
            v = " ".join(rng.choice(_WORDS) for _ in range(rng.randint(2, 5)))
            op = rng.choice(["contains", "=", "!="])
            out.append(f"{f} {op} {v}")
        else:
            f = rng.choice(_NUM_FIELDS)
            op = rng.choice(_NUM_OPS)
            v = f"{rng.uniform(0.0, 1e6):.5f}"
            out.append(f"{f} {op} {v}")
    return out


# Pre-built workloads (setup never timed).
_MIXED_A = _mixed(1500, 0)
_CONTAINS_A = _contains(2000, 1)
_NUMERIC_A = _numeric(8000, 2)
_MIXED_B = _mixed(12000, 3)
_NUMERIC_B = _numeric(15000, 4)
_CONTAINS_B = _contains(6000, 5, max_words=5)
_STRING_EQ = _string_eq(10000, 6)
_LONG_VALUES = _long_values(8000, 7)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def checks():
    return [
        ("empty", lambda: ([],)),
        ("single-condition", lambda: (["price < 100"],)),
        ("invalid-format", lambda: (["price"],)),
    ]


def cases():
    return [
        ("mixed-1500", lambda: (_MIXED_A,)),
        ("contains-2000", lambda: (_CONTAINS_A,)),
        ("numeric-8000", lambda: (_NUMERIC_A,)),
        ("mixed-12000", lambda: (_MIXED_B,)),
        ("numeric-15000", lambda: (_NUMERIC_B,)),
        ("contains-6000-multiword", lambda: (_CONTAINS_B,)),
        ("string-eq-10000", lambda: (_STRING_EQ,)),
        ("long-values-8000", lambda: (_LONG_VALUES,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['numeric-15000', 'mixed-12000', 'long-values-8000', 'string-eq-10000']
_KEEP_CHECKS = ['empty', 'single-condition', 'invalid-format']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
