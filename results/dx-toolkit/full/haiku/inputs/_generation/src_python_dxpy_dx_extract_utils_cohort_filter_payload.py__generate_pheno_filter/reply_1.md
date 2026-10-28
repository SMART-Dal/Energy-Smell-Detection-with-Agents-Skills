```python
import random

from dxpy.dx_extract_utils.cohort_filter_payload import generate_pheno_filter


def _conv(a, b):
    # Same conversion the repository's own test passes in.
    return a + [str(b)]


_ENTITY = "patient"
_FIELD = "patient_id"
_EF = "patient$patient_id"


def _rand_ids(n, seed):
    rng = random.Random(seed)
    return [f"id{rng.randrange(10 ** 12):012d}" for _ in range(n)]


def _values_and_primary(n_values, n_primary, overlap, seed):
    """A `values` list and a `primary` list sharing exactly `overlap` items."""
    rng = random.Random(seed)
    total = n_values + n_primary - overlap
    pool = [f"id{rng.randrange(10 ** 12):012d}" for _ in range(total)]
    values = pool[:n_values]
    primary = pool[n_values - overlap:n_values - overlap + n_primary]
    return values, primary


# ---------------------------------------------------------------------------
# shared, read-only data (built once)
# ---------------------------------------------------------------------------
_V1, _P1 = _values_and_primary(80_000, 2_000, 1_500, 1)   # "in"
_V2, _P2 = _values_and_primary(80_000, 2_000, 1_500, 2)   # "not-in"
_V3, _P3 = _values_and_primary(60_000, 3_000, 2_000, 3)   # "exists" + "in"
_V4, _P4 = _values_and_primary(50_000, 2_500, 2_000, 4)   # multi compound, match later
_V5 = _rand_ids(50_000, 5)                                # entity-name match
_V6 = _rand_ids(50_000, 6)                                # same entity, other field
_V7 = _rand_ids(80_000, 7)                                # no pheno_filters at all
_V8 = _rand_ids(80_000, 8)                                # non-compound pheno_filter


# ---------------------------------------------------------------------------
# thunks: fresh mutable `filters` on every call, big lists shared
# ---------------------------------------------------------------------------
def _case1():
    filters = {"pheno_filters": {"compound": [
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [{"condition": "in", "values": _P1}]}}
    ], "logic": "and"}}
    return (_V1, _ENTITY, _FIELD, filters, _conv)


def _case2():
    filters = {"pheno_filters": {"compound": [
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [{"condition": "not-in", "values": _P2}]}}
    ], "logic": "and"}}
    return (_V2, _ENTITY, _FIELD, filters, _conv)


def _case3():
    filters = {"pheno_filters": {"compound": [
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [
             {"condition": "exists"},
             {"condition": "in", "values": _P3},
         ]}}
    ], "logic": "and"}}
    return (_V3, _ENTITY, _FIELD, filters, _conv)


def _case4():
    compound = [
        {"name": "phenotype", "logic": "and",
         "filters": {"patient$other": [{"condition": "in", "values": ["a"]}]}},
        {"name": "phenotype", "logic": "and",
         "filters": {"sample$id": [{"condition": "in", "values": ["b"]}]}},
        {"name": "phenotype", "logic": "and"},
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [{"condition": "in", "values": _P4}]}},
    ]
    filters = {"pheno_filters": {"compound": compound, "logic": "and"}}
    return (_V4, _ENTITY, _FIELD, filters, _conv)


def _case5():
    compound = [{"name": "phenotype", "logic": "and",
                 "filters": {"sample$id": [{"condition": "in", "values": ["x"]}]}}
                for _ in range(100)]
    compound.append({"name": "phenotype", "logic": "and",
                     "entity": {"name": "patient"},
                     "filters": {"sample$id": [{"condition": "in", "values": ["x"]}]}})
    filters = {"pheno_filters": {"compound": compound, "logic": "and"}}
    return (_V5, _ENTITY, _FIELD, filters, _conv)


def _case6():
    compound = []
    for _ in range(200):
        compound.append({
            "name": "phenotype", "logic": "and",
            "filters": {f"sample$field{j}": [{"condition": "in", "values": ["x"]}]
                        for j in range(10)},
        })
    compound.append({
        "name": "phenotype", "logic": "and",
        "filters": {"patient$other_field": [{"condition": "in", "values": ["x"]}]},
    })
    filters = {"pheno_filters": {"compound": compound, "logic": "and"}}
    return (_V6, _ENTITY, _FIELD, filters, _conv)


def _case7():
    return (_V7, _ENTITY, _FIELD, {}, _conv)


def _case8():
    filters = {"pheno_filters": {"condition": "in", "values": ["a", "b"]}}
    return (_V8, _ENTITY, _FIELD, filters, _conv)


def checks():
    return [
        ("empty-values-empty-filters",
         lambda: ([], _ENTITY, _FIELD, {}, _conv)),
        ("non-and-logic-raises",
         lambda: (["a"], _ENTITY, _FIELD,
                  {"pheno_filters": {"compound": [], "logic": "or"}}, _conv)),
        ("non-compound-pheno-filter",
         lambda: (["a", "b"], _ENTITY, _FIELD,
                  {"pheno_filters": {"condition": "in", "values": ["a"]}}, _conv)),
    ]


def cases():
    return [
        ("in-large-values", _case1),
        ("not-in-large-values", _case2),
        ("exists-plus-in", _case3),
        ("multi-compound-match-later", _case4),
        ("entity-name-match", _case5),
        ("same-entity-other-field", _case6),
        ("no-pheno-filters", _case7),
        ("non-compound-wrap", _case8),
    ]
```