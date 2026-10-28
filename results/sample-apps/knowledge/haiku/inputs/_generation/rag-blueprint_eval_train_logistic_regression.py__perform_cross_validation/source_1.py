import csv
import random

from train_logistic_regression import perform_cross_validation


def _write_csv(path, n_rows, n_features, seed, pos_ratio=0.5, feature_scales=None, signal=1.0):
    rng = random.Random(seed)
    if feature_scales is None:
        feature_scales = [1.0] * n_features
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        header = (
            ["doc_id", "query_id", "relevance_score", "relevance_label"]
            + [f"feature_{j}" for j in range(n_features)]
        )
        writer.writerow(header)
        for i in range(n_rows):
            label = 1 if rng.random() < pos_ratio else 0
            row = [f"doc{i}", f"q{i // 10}", round(rng.random(), 4), label]
            for j in range(n_features):
                scale = feature_scales[j]
                val = rng.gauss(0.0, 1.0) * scale
                val += label * signal * scale * 0.5
                if j % 3 == 0:
                    val += rng.expovariate(1.0) * scale * 0.2
                row.append(val)
            writer.writerow(row)


_CASE_SPECS = [
    ("small-baseline", 800, 8, 0, 0.50, None, 1.0),
    ("medium-15f", 1500, 15, 1, 0.30, None, 1.0),
    ("wide-30f", 1200, 30, 2, 0.20, None, 0.8),
    ("large-2500", 2500, 10, 3, 0.40, None, 1.2),
    ("imbalanced", 2000, 12, 4, 0.05, None, 1.5),
    ("high-dim", 1000, 40, 5, 0.50, None, 0.7),
    ("noisy", 1800, 20, 6, 0.50, None, 0.1),
    (
        "scaled-features",
        1500,
        12,
        7,
        0.35,
        [10.0 ** rng for rng in [-3, -2, -1, 0, 1, 2, 3, -1, 0, 1, 2, 0]],
        1.0,
    ),
]

_CASE_INPUTS = []
for _label, _n_rows, _n_features, _seed, _pos, _scales, _signal in _CASE_SPECS:
    _csv_path = WORKDIR / f"cv_{_label}.csv"
    _coef_path = WORKDIR / f"cv_{_label}_coefficients.txt"
    _write_csv(
        _csv_path,
        _n_rows,
        _n_features,
        _seed,
        pos_ratio=_pos,
        feature_scales=_scales,
        signal=_signal,
    )
    _CASE_INPUTS.append((_label, str(_csv_path), str(_coef_path)))

_CHECK_EMPTY = WORKDIR / "cv_check_empty.csv"
_CHECK_ONE = WORKDIR / "cv_check_one.csv"
_CHECK_MISSING = WORKDIR / "cv_check_missing.csv"

_write_csv(_CHECK_EMPTY, 0, 3, 100)
_write_csv(_CHECK_ONE, 1, 1, 101, pos_ratio=1.0)
if _CHECK_MISSING.exists():
    _CHECK_MISSING.unlink()


def checks():
    return [
        ("empty-file", lambda: (str(_CHECK_EMPTY), None)),
        ("one-row", lambda: (str(_CHECK_ONE), None)),
        ("missing-file", lambda: (str(_CHECK_MISSING), None)),
    ]


def cases():
    return [
        (label, lambda p=csv_path, c=coef_path: (p, c))
        for label, csv_path, coef_path in _CASE_INPUTS
    ]
