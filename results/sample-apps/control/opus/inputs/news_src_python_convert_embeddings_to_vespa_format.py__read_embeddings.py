# Inputs for news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from convert_embeddings_to_vespa_format import read_embeddings

_DATA = WORKDIR / "embeddings_data"
_DATA.mkdir(parents=True, exist_ok=True)


def _write_plain(name, n, dim, seed, prefix="U", dup_ratio=0.0):
    rng = random.Random(seed)
    path = _DATA / name
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            if dup_ratio and i > 0 and rng.random() < dup_ratio:
                uid = "{}{:07d}".format(prefix, rng.randrange(i))
            else:
                uid = "{}{:07d}".format(prefix, i)
            vec = ",".join("{:.6f}".format(rng.uniform(-1.0, 1.0)) for _ in range(dim))
            f.write(uid + "\t" + vec + "\n")
    return str(path)


def _write_mixed(name, n, dim, seed):
    rng = random.Random(seed)
    path = _DATA / name
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            uid = "N{:07d}".format(i)
            parts = []
            for _ in range(dim):
                r = rng.random()
                if r < 0.25:
                    parts.append(str(rng.randint(-100, 100)))
                elif r < 0.50:
                    parts.append("{:.3e}".format(rng.uniform(-1.0, 1.0)))
                elif r < 0.75:
                    parts.append("{:.2f}".format(rng.uniform(-10.0, 10.0)))
                else:
                    parts.append("{:.8f}".format(rng.uniform(-1.0, 1.0)))
            f.write(uid + "\t" + ",".join(parts) + "\n")
    return str(path)


# Realistic embedding files: id<TAB>comma-separated vector, one per line.
_F1 = _write_plain("news_128d_500.tsv", 500, 128, 0, prefix="N")
_F2 = _write_plain("short_8d_8000.tsv", 8000, 8, 1, prefix="U")
_F3 = _write_plain("long_256d_200.tsv", 200, 256, 2, prefix="N")
_F4 = _write_plain("dup_16d_3000.tsv", 3000, 16, 3, prefix="U", dup_ratio=0.3)
_F5 = _write_plain("mid_64d_1500.tsv", 1500, 64, 4, prefix="N")
_F6 = _write_plain("tiny_2d_20000.tsv", 20000, 2, 5, prefix="U")
_F7 = _write_plain("wide_512d_100.tsv", 100, 512, 6, prefix="N")
_F8 = _write_mixed("mixed_64d_1000.tsv", 1000, 64, 7)

# Small edge files for checks().
_EMPTY = _DATA / "empty.tsv"
_EMPTY.write_text("", encoding="utf-8")
_SINGLE = _DATA / "single.tsv"
_SINGLE.write_text("U0000001\t0.5\n", encoding="utf-8")
_EMPTYID = _DATA / "emptyid.tsv"
_EMPTYID.write_text("\t1.0,2.0,3.0\n", encoding="utf-8")


def checks():
    return [
        ("empty-file", lambda: (str(_EMPTY),)),
        ("single-vector", lambda: (str(_SINGLE),)),
        ("empty-id", lambda: (str(_EMPTYID),)),
    ]


def cases():
    return [
        ("news-128d-500", lambda: (_F1,)),
        ("short-8d-8000", lambda: (_F2,)),
        ("long-256d-200", lambda: (_F3,)),
        ("duplicate-ids-16d-3000", lambda: (_F4,)),
        ("mid-64d-1500", lambda: (_F5,)),
        ("tiny-2d-20000", lambda: (_F6,)),
        ("wide-512d-100", lambda: (_F7,)),
        ("mixed-format-64d-1000", lambda: (_F8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['tiny-2d-20000', 'short-8d-8000', 'mid-64d-1500', 'duplicate-ids-16d-3000']
_KEEP_CHECKS = ['empty-file', 'single-vector', 'empty-id']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
