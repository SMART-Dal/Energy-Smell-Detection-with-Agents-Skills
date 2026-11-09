import random

from dxpy.bindings.apollo.dataset import Dataset


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


def _make_dataset(assays):
    ds = Dataset("dataset-0000")
    # The property reads its data from this cached field; setting it means no
    # network / file access is needed to obtain the descriptor file contents.
    ds._descriptor_file_dict = {"assays": assays}
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
