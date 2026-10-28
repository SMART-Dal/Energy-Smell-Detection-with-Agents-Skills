import random


def _list_conv(acc, item):
    # Mirrors the repository's lambda_for_list_conv: reduce(lambda a, b: a + [str(b)], ...)
    return acc + [str(item)]


# ---------------------------------------------------------------------------
# Shared, read-only data (built once; the function never mutates these lists).
# ---------------------------------------------------------------------------
_POOL = [f"patient_{i}" for i in range(400_000)]


def _sample(n, seed):
    return random.Random(seed).sample(_POOL, n)


ENTITY = "patient"
FIELD = "patient_id"
EF = "patient$patient_id"

V_50K = _sample(50_000, 0)
V_100K = _sample(100_000, 1)
V_120K = _sample(120_000, 2)
V_150K = _sample(150_000, 3)

# "existing" filter value lists are kept small: the repository's list-conv
# lambda is quadratic (acc + [x]), so a big existing list would be catastrophic.
EX_A = _sample(500, 10)
EX_B = _sample(500, 11)
EX_C = [_sample(500, 20 + i) for i in range(5)]
EX_D = [_sample(500, 30 + i) for i in range(6)]
EX_E = _sample(2000, 40)

_MIX_CONDS = ["in", "not-in", "in", "not-in", "in", "not-in"]


# ---------------------------------------------------------------------------
# Fresh (cheap) filter structures.  The function mutates `filters`, so every
# thunk call must hand it a brand new structure; the big value lists above are
# only referenced, never copied.
# ---------------------------------------------------------------------------
def _mk_wrapped():
    # pheno_filters without "compound" -> the function has to wrap it first.
    return {
        "pheno_filters": {
            "name": "phenotype",
            "logic": "and",
            "filters": {EF: [{"condition": "in", "values": EX_A}]},
        }
    }


def _mk_notin():
    return {
        "pheno_filters": {
            "compound": [
                {
                    "name": "phenotype",
                    "logic": "and",
                    "filters": {EF: [{"condition": "not-in", "values": EX_B}]},
                }
            ],
            "logic": "and",
        }
    }


def _mk_multi_in():
    return {
        "pheno_filters": {
            "compound": [
                {
                    "name": "phenotype",
                    "logic": "and",
                    "filters": {
                        EF: [{"condition": "in", "values": v} for v in EX_C]
                    },
                }
            ],
            "logic": "and",
        }
    }


def _mk_mixed():
    return {
        "pheno_filters": {
            "compound": [
                {
                    "name": "phenotype",
                    "logic": "and",
                    "filters": {
                        EF: [
                            {"condition": c, "values": v}
                            for c, v in zip(_MIX_CONDS, EX_D)
                        ]
                    },
                }
            ],
            "logic": "and",
        }
    }


def _mk_exists_and_in():
    return {
        "pheno_filters": {
            "compound": [
                {
                    "name": "phenotype",
                    "logic": "and",
                    "filters": {
                        EF: [
                            {"condition": "exists", "values": EX_A},
                            {"condition": "in", "values": EX_E},
                        ]
                    },
                }
            ],
            "logic": "and",
        }
    }


# Padding compound filters for the "entity name" path.  They are shared and
# never mutated; only the compound *list* is copied per call.
_PAD_INNER = {"name": "other_entity"}
_PADDING = [{"entity": _PAD_INNER} for _ in range(20_000)]


def _mk_entity_match():
    compound = list(_PADDING)
    compound.append({"entity": {"name": ENTITY}, "logic": "and", "filters": {}})
    return {"pheno_filters": {"compound": compound, "logic": "and"}}


# Keys for the "same entity, different field" path.  Shared strings; only the
# outer dict is copied per call.
_OTHER_KEYS = {f"other{i}$some_field": EX_A for i in range(20_000)}


def _mk_same_entity_diff_field():
    other = dict(_OTHER_KEYS)
    other["patient$other_field"] = EX_A
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
                _mk_wrapped(),
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
        #    entity$field "in" filter intersects a large set with a small one.
        (
            "wrapped-in-intersection",
            lambda: (V_100K, ENTITY, FIELD, _mk_wrapped(), _list_conv),
        ),
        # 3. "not-in" condition -> large set difference.
        (
            "not-in-difference",
            lambda: (V_120K, ENTITY, FIELD, _mk_notin(), _list_conv),
        ),
        # 4. five chained "in" filters, each intersecting the running value set.
        (
            "multi-in",
            lambda: (V_100K, ENTITY, FIELD, _mk_multi_in(), _list_conv),
        ),
        # 5. alternating "in" / "not-in" filters.
        (
            "mixed-in-not-in",
            lambda: (V_150K, ENTITY, FIELD, _mk_mixed(), _list_conv),
        ),
        # 6. existing entity$field filter with an "exists" condition (pass) and
        #    an "in" condition (large intersection).
        (
            "exists-and-in",
            lambda: (V_100K, ENTITY, FIELD, _mk_exists_and_in(), _list_conv),
        ),
        # 7. no entity$field filter: scan a long compound list, then match on
        #    the entity name and add the field filter.
        (
            "entity-name-match",
            lambda: (V_50K, ENTITY, FIELD, _mk_entity_match(), _list_conv),
        ),
        # 8. no entity name: scan a big filters dict and match on a filter that
        #    uses the same entity but a different field.
        (
            "same-entity-different-field",
            lambda: (
                V_50K,
                ENTITY,
                FIELD,
                _mk_same_entity_diff_field(),
                _list_conv,
            ),
        ),
    ]
