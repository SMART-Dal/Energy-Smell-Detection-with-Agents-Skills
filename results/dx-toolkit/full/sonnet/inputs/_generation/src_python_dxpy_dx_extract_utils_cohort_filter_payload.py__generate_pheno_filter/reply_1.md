```python
import random


def _list_conv(acc, item):
    # Mirrors the repository's lambda_for_list_conv: reduce(lambda a, b: a + [str(b)], ...)
    return acc + [str(item)]


# ---------------------------------------------------------------------------
# Shared, reusable data (built once, never mutated by the function under test)
# ---------------------------------------------------------------------------
_POOL = [f"patient_{i}" for i in range(300_000)]


def _sample(n, seed):
    return random.Random(seed).sample(_POOL, n)


ENTITY = "patient"
FIELD = "patient_id"
EF = "patient$patient_id"

V_50K = _sample(50_000, 0)
V_80K = _sample(80_000, 1)
V_100K = _sample(100_000, 2)
FV_80K_A = _sample(80_000, 3)
FV_80K_B = _sample(80_000, 4)
FV_60K = [_sample(60_000, 10 + i) for i in range(5)]
FV_60K_MIX = [_sample(60_000, 20 + i) for i in range(6)]

_SMALL_IN = [{"condition": "in", "values": ["x"]}]
_MIX_CONDS = ["in", "not-in", "in", "not-in", "in", "not-in"]


# ---------------------------------------------------------------------------
# Fresh filter structures (the function mutates its `filters` argument, so
# every thunk call must hand it a brand new structure; the big value lists
# are reused because the function never mutates them).
# ---------------------------------------------------------------------------
def _mk_compound(primary_filters):
    return {
        "pheno_filters": {
            "compound": [
                {"name": "phenotype", "logic": "and", "filters": {EF: primary_filters}}
            ],
            "logic": "and",
        }
    }


def _mk_wrapped_in():
    # pheno_filters without "compound" -> the function has to wrap it first.
    return {
        "pheno_filters": {
            "name": "phenotype",
            "logic": "and",
            "filters": {EF: [{"condition": "in", "values": FV_80K_A}]},
        }
    }


def _mk_entity_match(n_pad):
    compound = [{"name": "phenotype", "logic": "and"} for _ in range(n_pad)]
    compound.append({"entity": {"name": ENTITY}, "logic": "and", "filters": {}})
    return {"pheno_filters": {"compound": compound, "logic": "and"}}


def _mk_same_entity_diff_field(n_keys):
    other = {f"other{i}$some_field": _SMALL_IN for i in range(n_keys)}
    other["patient$other_field"] = _SMALL_IN
    return {
        "pheno_filters": {
            "compound": [
                {"name": "phenotype", "logic": "and", "filters": other}
            ],
            "logic": "and",
        }
    }


def checks():
    return [
        # no pheno_filters at all, empty values
        ("empty-filters", lambda: ([], ENTITY, FIELD, {}, _list_conv)),
        # existing "in" filter, empty values
        (
            "empty-values",
            lambda: (
                [],
                ENTITY,
                FIELD,
                _mk_compound([{"condition": "in", "values": ["a", "b"]}]),
                _list_conv,
            ),
        ),
        # compound pheno_filter with "or" logic -> raises ValueError
        (
            "bad-logic",
            lambda: (
                ["a"],
                ENTITY,
                FIELD,
                {"pheno_filters": {"compound": [], "logic": "or"}},
                _list_conv,
            ),
        ),
    ]


def cases():
    return [
        # 1. no pheno_filters key: creates the compound filter and appends a new
        #    entity filter carrying a large value list.
        (
            "create-new-entity-filter",
            lambda: (V_50K, ENTITY, FIELD, {}, _list_conv),
        ),
        # 2. existing pheno_filter is not compound -> gets wrapped, then the
        #    entity$field "in" filter intersects two large sets.
        (
            "wrapped-in-intersection",
            lambda: (V_80K, ENTITY, FIELD, _mk_wrapped_in(), _list_conv),
        ),
        # 3. "not-in" condition -> large set difference.
        (
            "not-in-difference",
            lambda: (
                V_80K,
                ENTITY,
                FIELD,
                _mk_compound([{"condition": "not-in", "values": FV_80K_B}]),
                _list_conv,
            ),
        ),
        # 4. "exists" condition -> no set work, only the append path.
        (
            "exists-condition",
            lambda: (
                V_50K,
                ENTITY,
                FIELD,
                _mk_compound([{"condition": "exists", "values": FV_80K_A}]),
                _list_conv,
            ),
        ),
        # 5. five chained "in" filters -> five large intersections in a row.
        (
            "multi-in",
            lambda: (
                V_100K,
                ENTITY,
                FIELD,
                _mk_compound([{"condition": "in", "values": v} for v in FV_60K]),
                _list_conv,
            ),
        ),
        # 6. alternating "in" / "not-in" filters.
        (
            "mixed-in-not-in",
            lambda: (
                V_100K,
                ENTITY,
                FIELD,
                _mk_compound(
                    [
                        {"condition": c, "values": v}
                        for c, v in zip(_MIX_CONDS, FV_60K_MIX)
                    ]
                ),
                _list_conv,
            ),
        ),
        # 7. no entity$field filter: match on the entity name, deep in a long
        #    list of compound filters.
        (
            "entity-name-match",
            lambda: (V_50K, ENTITY, FIELD, _mk_entity_match(20_000), _list_conv),
        ),
        # 8. no entity name: match on a filter that uses the same entity but a
        #    different field, scanning a big filters dict.
        (
            "same-entity-different-field",
            lambda: (
                V_50K,
                ENTITY,
                FIELD,
                _mk_same_entity_diff_field(20_000),
                _list_conv,
            ),
        ),
    ]
```