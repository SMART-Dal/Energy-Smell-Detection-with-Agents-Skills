import random


def _build(n_select, n_return, n_kwargs, seed, distinct=False):
    """Build a (sql, return_columns, kwargs) triple in the exact named-expression
    format the function itself emits: `table`.`column` AS `alias`."""
    rng = random.Random(seed)

    parts = []
    aliases = []
    for i in range(n_select):
        col = "c%d" % i
        alias = rng.choice(["a%d" % i, col, "alias_%d" % i])
        aliases.append(alias)
        parts.append("`allele`.`%s` AS `%s`" % (col, alias))

    sql = ("SELECT " + ("DISTINCT " if distinct else "") + ", ".join(parts)
           + " FROM `allele` JOIN `ref` ON `allele`.`locus_id` = `ref`.`locus_id`")

    kwargs = {}
    kw_names = []
    for i in range(n_kwargs):
        name = "k%d" % i
        kw_names.append(name)
        kwargs[name] = ("tbl%d" % i, "col%d" % i)

    return_columns = []
    for i in range(n_return):
        r = rng.random()
        if r < 0.45 and aliases:
            name = rng.choice(aliases)          # hit: present in SELECT list
        elif r < 0.75 and kw_names:
            name = rng.choice(kw_names)         # hit: supplied through kwargs
        else:
            name = "miss%d" % i                 # miss: becomes NULL
        return_columns.append((name,))

    return sql, return_columns, kwargs


_CASES = [
    ("small-mixed",        _build(100,   150,    5, 0, False)),
    ("medium-mixed",       _build(800,   1200,  20, 1, False)),
    ("distinct-medium",    _build(600,   900,   10, 2, True)),
    ("large-mixed",        _build(3000,  4000,  50, 3, False)),
    ("mostly-null",        _build(60,    6000,   0, 4, False)),
    ("many-kwargs",        _build(400,   1500, 800, 5, False)),
    ("huge-mixed",         _build(12000, 15000, 100, 6, False)),
    ("distinct-huge",      _build(9000,  12000, 300, 7, True)),
]


def _thunk(case):
    sql, return_columns, kwargs = case
    return lambda: call(sql, return_columns, **kwargs)


def checks():
    simple = "SELECT `t`.`a` AS `a` FROM `t`"
    return [
        ("empty-return-columns", lambda: (simple, [])),
        ("single-column",        lambda: (simple, [("a",)])),
        ("distinct-with-kwarg",  lambda: call(
            "SELECT DISTINCT `t`.`a` AS `a` FROM `t`",
            [("a",), ("b",)],
            b=("t", "b"),
        )),
    ]


def cases():
    return [(label, _thunk(case)) for label, case in _CASES]
