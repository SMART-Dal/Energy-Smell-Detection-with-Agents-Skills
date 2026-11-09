```python
import os
import random
import convert_embeddings_to_vespa_format as mod
from convert_embeddings_to_vespa_format import convert_news_embeddings


def _write_tsv(path, n, dim, seed, value_range=(-1.0, 1.0), zero_ratio=0.0, id_prefix="news"):
    rng = random.Random(seed)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            vals = []
            for _ in range(dim):
                if zero_ratio > 0 and rng.random() < zero_ratio:
                    vals.append(0.0)
                else:
                    vals.append(rng.uniform(*value_range))
            vec = ",".join("%.6f" % v for v in vals)
            f.write(f"{id_prefix}{i}\t{vec}\n")


_CASES = [
    ("tiny", 10, 10, 0, (-1.0, 1.0), 0.0),
    ("small", 100, 50, 1, (-1.0, 1.0), 0.0),
    ("medium", 1000, 50, 2, (-1.0, 1.0), 0.0),
    ("wide", 200, 300, 3, (-1.0, 1.0), 0.0),
    ("long", 5000, 10, 4, (-1.0, 1.0), 0.0),
    ("large_values", 800, 100, 5, (-1000.0, 1000.0), 0.0),
    ("small_values", 800, 100, 6, (-1e-6, 1e-6), 0.0),
    ("sparse", 1000, 50, 7, (-1.0, 1.0), 0.5),
]

_INPUT_FILES = {}
_OUTPUT_FILES = {}

for label, n, dim, seed, vr, zr in _CASES:
    inp = WORKDIR / f"news_embeddings_{label}.tsv"
    out = WORKDIR / f"vespa_news_embeddings_{label}.json"
    _INPUT_FILES[label] = inp
    _OUTPUT_FILES[label] = out
    _write_tsv(inp, n, dim, seed, value_range=vr, zero_ratio=zr)


def _make_thunk(inp, out):
    def thunk():
        mod.news_embeddings_file = str(inp)
        mod.news_embeddings_vespa = str(out)
        return ()
    return thunk


def cases():
    return [
        (label, _make_thunk(_INPUT_FILES[label], _OUTPUT_FILES[label]))
        for label, _, _, _, _, _ in _CASES
    ]


_CHECK_CASES = [
    ("empty", 0, 1, 0, (-1.0, 1.0), 0.0),
    ("one_dim_one", 1, 1, 0, (-1.0, 1.0), 0.0),
]

_CHECK_FILES = {}
for label, n, dim, seed, vr, zr in _CHECK_CASES:
    inp = WORKDIR / f"news_embeddings_check_{label}.tsv"
    out = WORKDIR / f"vespa_news_embeddings_check_{label}.json"
    _CHECK_FILES[label] = (inp, out)
    _write_tsv(inp, n, dim, seed, value_range=vr, zero_ratio=zr)

_malformed_inp = WORKDIR / "news_embeddings_check_malformed.tsv"
_malformed_out = WORKDIR / "vespa_news_embeddings_check_malformed.json"
_malformed_inp.write_text("no_tab_here\n")
_CHECK_FILES["malformed"] = (_malformed_inp, _malformed_out)


def checks():
    return [
        (label, _make_thunk(inp, out))
        for label, (inp, out) in _CHECK_FILES.items()
    ]
```