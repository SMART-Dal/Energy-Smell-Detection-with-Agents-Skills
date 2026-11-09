```python
import random


def _entries(n_samples, n_features, density, seed, extra=False, dup=1,
             feature_prefix="ENST", sample_prefix="sample_"):
    rng = random.Random(seed)
    entries = []
    for s in range(n_samples):
        sid = f"{sample_prefix}{s}"
        for f in range(n_features):
            if density < 1.0 and rng.random() >= density:
                continue
            fid = f"{feature_prefix}{f:08d}"
            for _ in range(dup):
                e = {
                    "feature_id": fid,
                    "sample_id": sid,
                    "expression": round(rng.uniform(0.0, 5000.0), 4),
                }
                if extra:
                    e["gene_name"] = f"GENE{f:05d}"
                    e["p_value"] = rng.random()
                    e["log2fc"] = rng.uniform(-5.0, 5.0)
                entries.append(e)
    return entries


def _mixed(seed):
    rng = random.Random(seed)
    entries = []
    pool = [f"ENST{i:011d}" for i in range(400)]
    for s in range(200):
        sid = f"sample_{s}"
        k = rng.randint(50, 400)
        feats = rng.sample(pool, k)
        for fid in feats:
            if rng.random() < 0.5:
                expr = rng.randint(0, 10**6)
            else:
                expr = round(rng.uniform(-100.0, 100.0), 6)
            entries.append({"feature_id": fid, "sample_id": sid, "expression": expr})
    rng.shuffle(entries)
    return entries


def _skewed(seed):
    rng = random.Random(seed)
    entries = []
    for s in range(300):
        sid = f"sample_{s}"
        entries.append({
            "feature_id": "ENST00000000",
            "sample_id": sid,
            "expression": round(rng.uniform(0.0, 100.0), 4),
        })
        for f in range(1, 250):
            if rng.random() < 0.3:
                entries.append({
                    "feature_id": f"ENST{f:08d}",
                    "sample_id": sid,
                    "expression": round(rng.uniform(0.0, 5000.0), 4),
                })
    return entries


_DENSE = _entries(300, 300, 1.0, 0)
_SPARSE = _entries(300, 300, 0.05, 1)
_WIDE = _entries(2000, 45, 1.0, 2)
_TALL = _entries(20, 4500, 1.0, 3)
_DUP = _entries(200, 200, 1.0, 4, dup=2)
_EXTRA = _entries(300, 250, 0.8, 5, extra=True)
_SKEW = _skewed(6)
_MIX = _mixed(7)


def checks():
    return [
        ("empty", lambda: ([],)),
        ("single", lambda: ([{"feature_id": "ENST00000001",
                              "sample_id": "sample_0",
                              "expression": 1.5}],)),
        ("none-expression", lambda: ([{"feature_id": "ENST00000001",
                                       "sample_id": "sample_0",
                                       "expression": None}],)),
    ]


def cases():
    return [
        ("dense-full", lambda: (list(_DENSE),)),
        ("sparse-5pct", lambda: (list(_SPARSE),)),
        ("many-samples", lambda: (list(_WIDE),)),
        ("few-samples-many-features", lambda: (list(_TALL),)),
        ("duplicated-entries", lambda: (list(_DUP),)),
        ("extra-keys", lambda: (list(_EXTRA),)),
        ("skewed-feature", lambda: (list(_SKEW),)),
        ("mixed-shuffled", lambda: (list(_MIX),)),
    ]
```