import random

import convert_embeddings_to_vespa_format as _mod
from convert_embeddings_to_vespa_format import convert_user_embeddings  # noqa: F401


def _write_tsv(path, n_users, dim, seed, id_fmt="{}", lo=-1.0, hi=1.0):
    rng = random.Random(seed)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n_users):
            vals = ",".join("%.6f" % rng.uniform(lo, hi) for _ in range(dim))
            f.write("%s\t%s\n" % (id_fmt.format(i), vals))
    return path


_DIR = WORKDIR

# ---- measured inputs (built once, before timing) ----
_F1 = _write_tsv(_DIR / "emb_small.tsv", 500, 64, 0)
_F2 = _write_tsv(_DIR / "emb_wide.tsv", 2000, 128, 1)
_F3 = _write_tsv(_DIR / "emb_narrow.tsv", 5000, 32, 2)
_F4 = _write_tsv(_DIR / "emb_deep.tsv", 1000, 300, 3)
_F5 = _write_tsv(_DIR / "emb_many.tsv", 8000, 8, 4, id_fmt="user_{}", lo=0.0, hi=1.0)
_F6 = _write_tsv(_DIR / "emb_bert.tsv", 300, 768, 5, id_fmt="doc-{}")
_F7 = _write_tsv(_DIR / "emb_big.tsv", 100, 1024, 6, lo=-100.0, hi=100.0)
_F8 = _write_tsv(_DIR / "emb_huge.tsv", 15000, 4, 7)

# ---- small edge inputs (checked only) ----
_C1 = _write_tsv(_DIR / "emb_empty.tsv", 0, 8, 8)
_C2 = _write_tsv(_DIR / "emb_one.tsv", 1, 1, 9)
_C3 = _write_tsv(_DIR / "emb_odd.tsv", 2, 3, 10, id_fmt="ünïcødé_{}")


def _runner(inp, out):
    def thunk():
        _mod.user_embeddings_file = str(inp)
        _mod.user_embeddings_vespa = str(out)
        return ()
    return thunk


def checks():
    return [
        ("empty-file", _runner(_C1, _DIR / "out_empty.json")),
        ("single-1d", _runner(_C2, _DIR / "out_one.json")),
        ("odd-ids", _runner(_C3, _DIR / "out_odd.json")),
    ]


def cases():
    return [
        ("small-64d", _runner(_F1, _DIR / "out_small.json")),
        ("wide-128d", _runner(_F2, _DIR / "out_wide.json")),
        ("narrow-32d", _runner(_F3, _DIR / "out_narrow.json")),
        ("deep-300d", _runner(_F4, _DIR / "out_deep.json")),
        ("many-8d", _runner(_F5, _DIR / "out_many.json")),
        ("bert-768d", _runner(_F6, _DIR / "out_bert.json")),
        ("big-1024d", _runner(_F7, _DIR / "out_big.json")),
        ("huge-4d", _runner(_F8, _DIR / "out_huge.json")),
    ]
