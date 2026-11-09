```python
import random

from dxpy.bindings.apollo.dataset import Dataset


# ---------------------------------------------------------------------------
# helpers to build realistic dataset detail-describe / descriptor structures
# ---------------------------------------------------------------------------

def _build_assays(spec, seed):
    """spec: list of (assay_type, count). Returns a flat list of assay dicts."""
    rng = random.Random(seed)
    out = []
    for assay_type, count in spec:
        for j in range(count):
            name = "%s_%d" % (assay_type, j)
            if rng.random() < 0.15:
                name = name + "_" + "x" * rng.randrange(1, 40)
            out.append({
                "name": name,
                "assay_type": assay_type,
                "type": assay_type,
                "assayType": assay_type,
                "assay_name": name,
                "generalized_assay_model_version": "v%d" % rng.randrange(1, 6),
                "version": "v%d" % rng.randrange(1, 6),
            })
    return out


def _group(assays):
    grouped = {}
    for assay in assays:
        grouped.setdefault(assay["assay_type"], []).append(assay)
    return grouped


def _make_dataset(assays):
    grouped = _group(assays)
    detail = {
        "id": "dataset-0000",
        "types": list(grouped.keys()),
        "details": {
            "descriptor": {"$dnanexus_link": "file-0000"},
            "assays": assays,
            "assays_info": grouped,
        },
        "assays": assays,
        "assays_info": grouped,
    }
    ds = Dataset("dataset-0000", detail)
    # make sure the detail describe is the one we built (no HTTP request)
    ds._detail_describe = detail
    # short-circuit the descriptor-file download so no network is touched
    descriptor_file_dict = {"assays": assays}
    ds._descriptor_file_dict = descriptor_file_dict
    ds.__dict__["descriptor_file_dict"] = descriptor_file_dict
    return ds


# ---------------------------------------------------------------------------
# module level inputs (built once, reused by every timed call)
# ---------------------------------------------------------------------------

_FIVE = ["molecular_expression", "genome_wide_expression", "proteomics",
         "metabolomics", "single_cell"]

_DS_SMALL = _make_dataset(_build_assays([("molecular_expression", 500)], 1))
_DS_THREE = _make_dataset(_build_assays(
    [("molecular_expression", 1000), ("genome_wide_expression", 1000),
     ("proteomics", 1000)], 2))
_DS_FIVE = _make_dataset(_build_assays([(t, 2400) for t in _FIVE], 3))
_DS_MISS = _make_dataset(_build_assays([(t, 1200) for t in _FIVE], 4))
_DS_MANY_TYPES = _make_dataset(_build_assays(
    [("assay_type_%d" % i, 160) for i in range(50)], 5))
_DS_ONE_HUGE = _make_dataset(_build_assays([("molecular_expression", 15000)], 6))
_DS_UNEVEN = _make_dataset(_build_assays(
    [("molecular_expression", 13000), ("proteomics", 800),
     ("metabolomics", 400), ("single_cell", 100)], 7))
_DS_LONG = _make_dataset(_build_assays([(t, 1600) for t in _FIVE], 8))


# ---------------------------------------------------------------------------
# checks: small edge inputs, only compared for identical behaviour
# ---------------------------------------------------------------------------

def checks():
    empty = _make_dataset([])
    one = _make_dataset(_build_assays([("molecular_expression", 1)], 99))
    return [
        ("no-assays", lambda: (empty, "molecular_expression")),
        ("single-assay", lambda: (one, "molecular_expression")),
        ("odd-type", lambda: (one, None)),
    ]


# ---------------------------------------------------------------------------
# cases: 8 measured inputs
# ---------------------------------------------------------------------------

def cases():
    return [
        ("single-type-small", lambda: (_DS_SMALL, "molecular_expression")),
        ("three-types", lambda: (_DS_THREE, "molecular_expression")),
        ("five-types-large", lambda: (_DS_FIVE, "proteomics")),
        ("missing-type", lambda: (_DS_MISS, "nonexistent_type")),
        ("many-types", lambda: (_DS_MANY_TYPES, "assay_type_7")),
        ("one-huge-type", lambda: (_DS_ONE_HUGE, "molecular_expression")),
        ("uneven-counts", lambda: (_DS_UNEVEN, "molecular_expression")),
        ("long-names", lambda: (_DS_LONG, "molecular_expression")),
    ]
```