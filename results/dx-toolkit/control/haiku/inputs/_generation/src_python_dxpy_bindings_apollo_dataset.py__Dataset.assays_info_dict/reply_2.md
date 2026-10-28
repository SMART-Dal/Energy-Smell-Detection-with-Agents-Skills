```python
import json
import random

from dxpy.bindings.apollo.dataset import Dataset

_DATASET_ID = "dataset-1f2g3h4i5j6k7l8m9n0p1q2r"


def _build_assays(n, n_models, seed, with_reference=True, with_version=True):
    rng = random.Random(seed)
    models = ["model_%d" % i for i in range(n_models)]
    assays = []
    for i in range(n):
        d = {
            "name": "assay_%d_%d" % (i, rng.randint(0, 10 ** 6)),
            "uuid": "uuid-%d-%d" % (i, rng.randint(0, 10 ** 9)),
            "generalized_assay_model": models[rng.randrange(n_models)],
        }
        if with_reference:
            d["reference"] = "ref_%d" % rng.randint(0, 10 ** 4)
        if with_version:
            d["generalized_assay_model_version"] = "v%d" % rng.randint(0, 9)
        assays.append(d)
    return assays


def _new_dataset():
    # Prefer the real constructor; fall back to __new__ if the record-id
    # validation rejects our synthetic id in this environment.
    try:
        return Dataset(_DATASET_ID)
    except Exception:
        pass
    ds = Dataset.__new__(Dataset)
    for attr, value in (
        ("dataset_id", _DATASET_ID),
        ("_dxid", _DATASET_ID),
        ("_detail_describe", None),
        ("_visualize_info", None),
    ):
        try:
            setattr(ds, attr, value)
        except Exception:
            pass
    return ds


def _make_dataset(assays):
    ds = _new_dataset()
    payload = {"assays": assays}
    # Set every plausible backing field so that <descriptor_file_dict> returns
    # our data without any network / filesystem access.
    for attr, value in (
        ("_descriptor_file_dict", payload),
        ("_descriptor_file", json.dumps(payload)),
        ("_detail_describe", {"details": {"descriptor_file_dict": payload}}),
    ):
        try:
            setattr(ds, attr, value)
        except Exception:
            pass
    return ds


# ---- module level data (built once, reused by every thunk call) ----
_A_TINY = _build_assays(10, 2, 0)
_A_MANY_FEW = _build_assays(8000, 3, 1)
_A_MANY_MANY = _build_assays(5000, 5000, 2)
_A_NO_OPT = _build_assays(6000, 20, 3, with_reference=False, with_version=False)
_A_REF_ONLY = _build_assays(7000, 15, 4, with_reference=True, with_version=False)
_A_VER_ONLY = _build_assays(7000, 15, 5, with_reference=False, with_version=True)
_A_LARGE_MIXED = _build_assays(10000, 100, 6)
_A_SINGLE_MODEL = _build_assays(9000, 1, 7)


def checks():
    return [
        ("empty-assays",
         lambda: (_make_dataset([]),)),
        ("single-assay-no-optionals",
         lambda: (_make_dataset([{"name": "a", "uuid": "u",
                                  "generalized_assay_model": "m"}]),)),
        ("missing-model-key",
         lambda: (_make_dataset([{"name": "a", "uuid": "u"}]),)),
    ]


def cases():
    return [
        ("tiny-two-models", lambda: (_make_dataset(_A_TINY),)),
        ("many-assays-few-models", lambda: (_make_dataset(_A_MANY_FEW),)),
        ("many-assays-many-models", lambda: (_make_dataset(_A_MANY_MANY),)),
        ("no-optional-fields", lambda: (_make_dataset(_A_NO_OPT),)),
        ("reference-only", lambda: (_make_dataset(_A_REF_ONLY),)),
        ("version-only", lambda: (_make_dataset(_A_VER_ONLY),)),
        ("large-mixed", lambda: (_make_dataset(_A_LARGE_MIXED),)),
        ("single-model", lambda: (_make_dataset(_A_SINGLE_MODEL),)),
    ]
```