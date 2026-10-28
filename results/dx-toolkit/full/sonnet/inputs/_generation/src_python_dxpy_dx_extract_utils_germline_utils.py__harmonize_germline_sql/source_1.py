import json
import os
import random

from dxpy.dx_extract_utils.filter_to_payload import extract_utils_basepath
from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql

# ---------------------------------------------------------------------------
# Read the return columns JSON so we know exactly which columns the function
# will try to add.  This is the same file the function itself opens.
# ---------------------------------------------------------------------------
_JSON_PATH = os.path.join(extract_utils_basepath, "return_columns_genotype.json")
with open(_JSON_PATH) as f:
    _RETURN_COLUMNS_RAW = json.load(f)
_RETURN_COLUMNS = [tuple(rc)[0] for rc in _RETURN_COLUMNS_RAW]


# ---------------------------------------------------------------------------
# Helpers for building realistic SQL strings
# ---------------------------------------------------------------------------
def _col_expr(table, column, alias=None):
    if alias is None:
        alias = column
    return f"`{table}`.`{column}` AS `{alias}`"


def _build_sql(select_exprs, distinct=False, pre="", post="", where="1=1"):
    distinct_str = "DISTINCT " if distinct else ""
    select_list = ", ".join(select_exprs)
    sql = (
        f"SELECT {distinct_str}{select_list} FROM `genotype` AS `g` "
        f"JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE {where}"
    )
    return pre + sql + post


# ---------------------------------------------------------------------------
# Build the 8 measured inputs once at module level.
# ---------------------------------------------------------------------------
rng = random.Random(0)

# 1. typical small query, a few return columns present, a few extras
_typical_cols = []
for i, rc in enumerate(_RETURN_COLUMNS[:5]):
    _typical_cols.append(_col_expr("g", f"col{i}", alias=rc))
for i in range(5):
    _typical_cols.append(_col_expr("g", f"col{100+i}", alias=f"extra_{rng.randint(0, 10**6)}"))
_typical_sql = _build_sql(_typical_cols)

# 2. large SELECT list (5000 columns)
_large_cols = [
    _col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}")
    for i in range(5000)
]
_large_sql = _build_sql(_large_cols)

# 3. same as typical but with DISTINCT
_distinct_sql = _build_sql(_typical_cols, distinct=True)

# 4. all return columns present, plus many extras
_all_ret_cols = []
for i, rc in enumerate(_RETURN_COLUMNS):
    _all_ret_cols.append(_col_expr("g", f"col{i}", alias=rc))
for i in range(2000 - len(_RETURN_COLUMNS)):
    _all_ret_cols.append(
        _col_expr("g", f"col{1000+i}", alias=f"extra_{rng.randint(0, 10**9)}")
    )
_all_ret_sql = _build_sql(_all_ret_cols)

# 5. no return columns present (all will be added as NULL)
_no_ret_cols = [
    _col_expr("g", f"col{i}", alias=f"none_{rng.randint(0, 10**9)}")
    for i in range(2000)
]
_no_ret_sql = _build_sql(_no_ret_cols)

# 6. "ref" not in the SELECT list -> exercises the kwargs branch for ref
_ref_cols = [
    _col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}")
    for i in range(1000)
]
_ref_sql = _build_sql(_ref_cols)


# 7. many joins before the matching ON ... WHERE clause
def _build_many_joins_sql(num_joins):
    select_list = ", ".join([f"`t0`.`col{i}` AS `col{i}`" for i in range(10)])
    sql = f"SELECT {select_list} FROM `table0` AS `t0`"
    for i in range(1, num_joins):
        sql += f" JOIN `table{i}` AS `t{i}` ON `t{i-1}`.`b_id` = `t{i}`.`b_id`"
    sql += " JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE 1=1"
    return sql


_many_joins_sql = _build_many_joins_sql(2000)

# 8. very long WHERE clause to stress the regex substitution
_long_where_cols = [
    _col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}")
    for i in range(2000)
]
_long_where_sql = _build_sql(_long_where_cols, where="x" * 500_000)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-join", lambda: ("SELECT * FROM genotype",)),
        ("join-no-select", lambda: ("ON `g`.`a_id` = `a`.`a_id` WHERE 1=1",)),
    ]


def cases():
    return [
        ("typical", lambda: (_typical_sql,)),
        ("large-select", lambda: (_large_sql,)),
        ("distinct", lambda: (_distinct_sql,)),
        ("all-return-columns", lambda: (_all_ret_sql,)),
        ("no-return-columns", lambda: (_no_ret_sql,)),
        ("ref-present", lambda: (_ref_sql,)),
        ("many-joins", lambda: (_many_joins_sql,)),
        ("long-where", lambda: (_long_where_sql,)),
    ]
