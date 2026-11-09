Let me look at the function. It takes `sql`, `return_columns`, `**kwargs`.

`_parse_sql_select_named_expression` uses NAMED_EXPRESSION_REGEX which isn't shown. Let me think about what it likely is.

SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"

NAMED_EXPRESSION_REGEX is unknown. The parse yields named_expression_match[1], [2], [4] as table, column, alias. So groups 1,2,4. Likely something like r"`?(\w+)`?\.`?(\w+)`?\s+AS\s+`?(\w+)`?" hmm but group 4.

Let me think: maybe `r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"` — that gives group1 = full, group2 = table, group3 = column, group4 = AS..., group5 = alias. That matches indices 1,2,4 for table, column, alias... no, group 4 would be the "AS `alias`" part, not alias.

Hmm. Maybe the regex is `r"(`?(\w+)`?\.`?(\w+)`?)(?:\s+AS\s+`?(\w+)`?)?"` — groups: 1=full, 2=table, 3=column, 4=alias. That matches perfectly: group 4 = alias. So NAMED_EXPRESSION_REGEX = something like r"(`?(\w+)`?\.`?(\w+)`?)(?:\s+AS\s+`?(\w+)`?)?".

Actually the real code from dx-toolkit. Let me recall... I can't recall exactly. Let me reason from the usage. In `harmonize_germline_sql`, the SELECT list is built with things like "`allele`.`locus_id` AS `locus_id`". And the return columns are like "locus_id". So the regex must handle backticks.

Let me guess: 
```python
NAMED_EXPRESSION_REGEX = r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"
```
Then group indices: 1 = whole table.column, 2 = table, 3 = column, 4 = " AS `alias`", 5 = alias. Then .groups()[4] would be the alias — but that's group 5 in 1-based, index 4 in 0-based. Yes! `.groups()` returns a tuple 0-based, so `[1]` = group 2 = table, `[2]` = group 3 = column, `[4]` = group 5 = alias. That works!

So NAMED_EXPRESSION_REGEX = r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?".

Hmm, but that requires the alias to be present, otherwise group 5 is None. In the harmonize function, it does `"`{table}`.`{column}` AS `{return_column}`".format(...)` — so table and column must be strings. If alias absent, it'd be None. But that's fine for our inputs.

Actually wait, maybe the regex is different. Let me consider the alternative where group 4 is the alias directly: `r"`?(\w+)`?\.`?(\w+)`?\s+AS\s+`?(\w+)`?"` gives group1=table, group2=column, group3=alias. Then [1],[2],[4] wouldn't work.

So the 5-group version seems right. Let me be safe and construct SQL that works with a plausible regex. Since we can't test, we need to be careful.

Actually, we could be defensive: the safest is to mimic what the repository generates. Let me think about what SQL looks like in this repo. The function is used in `harmonize_germline_sql`. Let me recall the dx-toolkit germline code.

Actually the safest approach: I should write SQL with backticks and AS clauses, like:
```
SELECT `allele`.`locus_id` AS `locus_id`, `allele`.`a_id` AS `a_id` FROM ...
```

For the regex `r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"`:
- On "`allele`.`locus_id` AS `locus_id`": group1 = "`allele`.`locus_id`", group2 = "allele", group3 = "locus_id", group4 = " AS `locus_id`", group5 = "locus_id". Good.

But hmm, `re.match` on the named expression which is stripped. OK.

Now the main regex `SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"`. Non-greedy `.+?` — matches minimal up to first " FROM". So the SELECT list must not contain " FROM" inside. Fine.

The function: `return_columns` is a list of columns, each is `tuple(return_column)[0]` — so it handles strings (tuple("abc")[0] = "a")... wait, tuple of a string gives characters, [0] = first char! Hmm. That seems odd. Unless return_columns are lists/tuples of one element. Actually in the repo, `genotype_return_columns` — let me think. `tuple(return_column)[0]` — if return_column is a string "locus_id", tuple gives ('l','o',...) and [0] = 'l'. That would be wrong. So return_columns must be a list of one-element tuples/lists, e.g. [("locus_id",), ("a_id",)]. Hmm, or maybe it's a dict... Actually `tuple(return_column)[0]` where return_column is a tuple ("locus_id",) gives "locus_id". 

Hmm, but in the call: `_harmonize_sql_select_named_expression(sql, genotype_return_columns, ref=(allele_table, "a_id"))`. So genotype_return_columns is a list of tuples presumably.

Actually wait — maybe genotype_return_columns is a list of strings and the code is buggy? Or maybe it's a list of tuples. Let me just use tuples of one element to be safe. Actually, to be safe, let's use tuples: `[("locus_id",), ("a_id",), ...]`.

Hmm, but actually if it's a list of strings, tuple(return_column)[0] gives first char, and then `return_column in select_info` would be checking a char. That would produce weird output but still run. But we want realistic. Let me use tuples.

Hmm, but actually let me reconsider. Maybe return_columns is a list where each element is a tuple like (name, type). `tuple(return_column)[0]` takes the first element = name. That makes sense! E.g. `[("locus_id", "string"), ("a_id", "int")]`. Yes, that's plausible.

OK. So we'll build return_columns as list of tuples.

Now kwargs: `ref=(allele_table, "a_id")`. So kwargs maps a column name to (table, column). The function uses `kwargs[return_column][0]` and `[1]`.

So for our inputs: sql with SELECT list, return_columns list of tuples, kwargs with some columns.

The output: a new SQL string. Output is a single string, fine.

Now let's design 8 cases with varying sizes. The function's work is proportional to number of return_columns and size of SQL. To make it take ~1ms to 200ms, we need many return_columns (thousands) or long SQL.

The regex sub with a large SQL string... re.sub on a large string is O(n). To get 200ms we might need a big string. Let's aim for moderate.

Let me think about the regex behavior more. `SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"`. re.sub replaces the matched "SELECT ... FROM" with "SELECT {distinct}{select_list} FROM". Note it replaces the whole match including "SELECT" and "FROM". Good.

Now, building the SQL: we need `_parse_sql_select_named_expression` to parse each comma-separated expression. So the SELECT list is comma-separated named expressions.

Let's construct SQL like:
```
SELECT `allele`.`locus_id` AS `locus_id`, `allele`.`a_id` AS `a_id`, ... FROM `allele` JOIN ...
```

Hmm, but the JOIN part — the regex `.+?\s+FROM` non-greedy will stop at the first " FROM". If the FROM clause is followed by JOIN with " ON ... WHERE", that's fine, it's after the match. The sub replaces only the SELECT...FROM portion.

Wait, but `re.sub` with the pattern will replace all matches. There's only one "SELECT ... FROM". Fine.

Actually careful: if the SQL contains " FROM" later (like in a subquery), non-greedy handles the first. Fine.

Now, to make it realistic and diverse:

Case 1: typical small - 20 select columns, 50 return columns, some in kwargs.
Case 2: many columns in SELECT (500), return_columns 500.
Case 3: DISTINCT variant.
Case 4: large SQL with huge select list.

The main cost: `_parse_sql_select_named_expression` does re.match per named expression, and the final re.sub over the whole sql. So cost ~ number of expressions + len(sql).

For 200ms we'd need maybe 10,000+ expressions. Let's test mentally: re.match on a short string ~ microseconds. 10,000 * few µs = tens of ms. Plus re.sub on a ~500KB string. That's fine.

Let's aim for cases with 100 to 5000 named expressions.

Also return_columns count matters: the loop is O(len(return_columns)).

Let's design:

- "small-typical": 10 select cols, 20 return cols, 1 kwarg.
- "medium-mixed": 200 select cols, 300 return cols, 50 kwargs.
- "large-many-columns": 2000 select cols, 3000 return cols, 500 kwargs.
- "distinct": 500 select cols, 500 return cols, DISTINCT.
- "mostly-null": few select cols, many return cols (most become NULL).
- "huge-sql": 5000 select cols, 5000 return cols.
- "wide-kwargs": 100 select cols, 1000 return cols with many kwargs.
- "duplicate-aliases"? Hmm, distinct aliases better.

Wait, need to be careful about total output size: output is one string. Fine, under 100000 values? It's a single string. The spec says keep return under 100000 values — a string is one value. Fine.

Input data under 1,000,000 values — the SQL string is one value. Fine.

Now, `checks()`: 2-3 small edge inputs. E.g. empty return_columns, single column, DISTINCT.

But careful: checks may raise. E.g. sql without FROM would raise AttributeError. Let's include a couple that run and maybe one odd.

Let's write:

checks:
- ("no-return-columns", lambda: (SELECT_SQL, []) ) — return_columns empty → select_list = "" → output "SELECT  FROM ..." hmm, `"SELECT {distinct}{select_list} FROM"` with empty select_list gives "SELECT  FROM". Fine, runs.
- ("single-column", lambda: ("SELECT `t`.`a` AS `a` FROM `t`", [("a",)]))
- ("distinct-single", lambda: ("SELECT DISTINCT `t`.`a` AS `a` FROM `t`", [("a",)]))

Now the main concern: the exact NAMED_EXPRESSION_REGEX. If my SQL doesn't match it, `re.match(...).groups()` would raise AttributeError (None has no groups) → the function raises → all cases fail. That's a big risk.

Let me try to recall the actual dx-toolkit source. The file is `src/python/dxpy/dx_extract_utils/germline_utils.py`. Let me think...

I recall something like:
```python
SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"
NAMED_EXPRESSION_REGEX = r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"
```

Hmm, I'm fairly confident about this pattern style. Let me think about `harmonize_germline_sql` more. Actually let me recall the broader germline_utils.py.

I think there's:
```python
def harmonize_germline_sql(sql):
    ...
    join_condition_regex = r"ON\s+`?(\w+)`?\.`?locus_id`?\s*=\s*`?(\w+)`?\.`?locus_id`?"
```
Not sure.

Given uncertainty, I should design SQL that matches many plausible regexes. The key: table.column with backticks and AS alias with backticks. That's the format the function itself produces: `` `{table}`.`{column}` AS `{return_column}` ``. So the regex must match exactly that format. Great — so I'll use exactly that format in the input SQL. That's the safest.

So each named expression: `` `allele`.`locus_id` AS `locus_id` ``.

For the regex `r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"`, this matches. Good.

But what if the regex requires no backticks? Unlikely given the output format uses backticks.

What if group 4 is the alias (4-group regex)? Then [1]=table,[2]=column,[4] would be out of range → IndexError. Hmm. But the code uses [4], so the regex must have at least 5 groups. So group 4 (0-indexed) exists, meaning >= 5 groups. With groups 1..5: 1=?, 2=table, 3=column, 4=?, 5=alias. So there's an extra group before table and between column and alias. The pattern `(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?` fits: group1 = whole, group2 = table, group3 = column, group4 = " AS alias", group5 = alias. 

Alternatively: `(`?(\w+)`?)\.(`?(\w+)`?)\s+AS\s+`?(\w+)`?` → group1 = table w/ backticks, group2 = table, group3 = column w/backticks, group4 = column, group5 = alias. Then [1]=table (with backticks!), [2]=column with backticks, [4]=alias. Hmm, that would give table = "`allele`" including backticks. Then the output would be "``allele``.`locus_id`". Possible but weird.

Hmm. Which is it? The output format string is `` "`{table}`.`{column}` AS `{return_column}`" `` — adding backticks around table and column. If table already had backticks, you'd get double backticks. So table/column should NOT include backticks. So group2 = table without backticks. So the first pattern is more likely.

Given the function adds backticks, the parse extracts unquoted names. So `\w+` groups for table and column. Good.

OK, I'm fairly confident. Let's go with the format: `` `table`.`column` AS `alias` ``.

Now, one more consideration: `re.match(NAMED_EXPRESSION_REGEX, named_expression)` — match from start. Our expression starts with backtick. The regex `` (`?(\w+)`?\.`?(\w+)`?)... `` — `? optional backtick, then \w+. Good.

Now let's think about whether the alias part is optional. In our SQL we always include " AS `alias`". Fine.

Now let's build SQL strings.

Helper to build a select list:
```python
def _select_list(n, seed, table="allele"):
    rng = random.Random(seed)
    parts = []
    for i in range(n):
        col = f"col{i}"  # or random names
        alias = f"col{i}"
        parts.append(f"`{table}`.`{col}` AS `{alias}`")
    return ", ".join(parts)
```

Hmm but we want diversity — some aliases not matching column names, some columns repeated, etc. But keep it valid.

We want the return_columns to hit some select aliases, some kwargs, some NULL.

Let's write a generator:

```python
def _make_case(n_select, n_return, n_kwargs, seed, distinct=False, table="allele"):
    rng = random.Random(seed)
    select_cols = []
    for i in range(n_select):
        col = f"c{i}"
        alias = f"a{i}" if rng.random() < 0.5 else col
        select_cols.append((col, alias))
    select_list = ", ".join(f"`{table}`.`{col}` AS `{alias}`" for col, alias in select_cols)
    ...
```

Hmm, but aliases should be unique-ish for the dict. Duplicate aliases just overwrite, fine.

return_columns: list of tuples. Some aliases from select, some from kwargs, some random (NULL).

kwargs: dict mapping name -> (table, column).

Let me write:

```python
def _build(n_select, n_return, n_kwargs, seed, distinct=False):
    rng = random.Random(seed)
    aliases = []
    parts = []
    for i in range(n_select):
        col = f"c{i}"
        alias = rng.choice([f"a{i}", col, f"alias_{i}"])
        aliases.append(alias)
        parts.append(f"`allele`.`{col}` AS `{alias}`")
    select_list = ", ".join(parts)
    distinct_sql = "DISTINCT " if distinct else ""
    sql = f"SELECT {distinct_sql}{select_list} FROM `allele` JOIN `ref` ON `allele`.`locus_id` = `ref`.`locus_id`"
    ...
```

Wait, but if the SQL contains " FROM" only once, fine. But `JOIN ... ON` after FROM. The regex `.+?\s+FROM` matches "SELECT ... FROM" up to first FROM. Good.

Actually careful: the non-greedy `.+?` combined with `\s+FROM` — it will find the earliest " FROM". Good.

Now return_columns: choose from aliases (hits), kwargs keys, and random misses.

```python
    return_columns = []
    for i in range(n_return):
        r = rng.random()
        if r < 0.5 and aliases:
            name = rng.choice(aliases)
        elif r < 0.75:
            name = f"k{i}"  # kwargs name
        else:
            name = f"miss{i}"
        return_columns.append((name,))
```

Hmm but kwargs names need to be consistent. Let me generate kwargs names first.

Let me restructure:

```python
def _build(n_select, n_return, n_kwargs, seed, distinct=False):
    rng = random.Random(seed)
    parts = []
    aliases = []
    for i in range(n_select):
        col = f"c{i}"
        alias = rng.choice([f"a{i}", col, f"alias_{i}"])
        aliases.append(alias)
        parts.append(f"`allele`.`{col}` AS `{alias}`")
    sql = "SELECT " + ("DISTINCT " if distinct else "") + ", ".join(parts) + " FROM `allele` JOIN `ref` ON `allele`.`locus_id` = `ref`.`locus_id`"
    kwargs = {}
    kw_names = []
    for i in range(n_kwargs):
        name = f"k{i}"
        kw_names.append(name)
        kwargs[name] = (f"tbl{i}", f"col{i}")
    return_columns = []
    for i in range(n_return):
        r = rng.random()
        if r < 0.45 and aliases:
            name = rng.choice(aliases)
        elif r < 0.75 and kw_names:
            name = rng.choice(kw_names)
        else:
            name = f"miss{i}"
        return_columns.append((name,))
    return sql, return_columns, kwargs
```

Then thunk: `lambda: (sql, return_columns, **kwargs)`? But we can't use `**kwargs` in a lambda easily... actually `lambda: call(sql, return_columns, **kwargs)` — the instructions say for keyword arguments the thunk returns `call(...)`. Hmm, but kwargs here are arbitrary names. We can use `call(sql, return_columns, **kwargs)`.

Wait, but the function signature is `_harmonize_sql_select_named_expression(sql, return_columns, **kwargs)`. The kwargs are the extra columns. So we pass them as keyword arguments. But their names are like "k0", "k1" — valid identifiers. Good.

So thunk: `lambda: call(sql, return_columns, **kwargs)`.

But careful: the function reads kwargs[return_column] — so return_column must equal a kwarg name. Good.

Now, is passing arbitrary kwargs OK? Yes.

Hmm, but the spec says "For keyword arguments the thunk returns `call(...)`". So we use `call`. Good.

Now, is `call` available in module scope? Yes, provided. Don't import.

Now sizes. Let's estimate timing.

Case with n_select=2000, n_return=3000: parsing 2000 expressions with re.match each (~1-2 µs) = few ms. The loop 3000 iterations. re.sub over sql of length ~ 2000*40 = 80KB. Probably ~5-10ms. Good.

To reach ~100ms, use n_select=20000, n_return=30000. SQL ~ 800KB. re.sub maybe 50ms. Hmm, might be OK. Let's be moderate: max around 10000 select, 15000 return.

Actually, let's think: the problem says one call should take 1ms-200ms. Let's have a spread: 50, 200, 500, 1000, 2000, 5000, 10000 select columns.

Let me define 8 cases:

1. "tiny-typical": n_select=8, n_return=15, n_kwargs=2, seed=0. ~1ms? Maybe less. Hmm, need at least 1ms ideally. Actually the requirement is roughly; small is fine as long as it's not dropped. The runner keeps the 4 that do the most work. So we need at least 4 substantial ones. Small ones are fine.

Let's make the smallest still ~1ms: n_select=200, n_return=300.

Actually let's just design a good spread:

1. "small": 100 select, 150 return, 5 kwargs, seed 0
2. "medium": 500 select, 800 return, 20 kwargs, seed 1
3. "distinct-medium": 500 select, 600 return, 10 kwargs, seed 2, distinct=True
4. "large": 2000 select, 3000 return, 50 kwargs, seed 3
5. "mostly-null": 50 select, 5000 return, 0 kwargs, seed 4  (most returns are NULL)
6. "many-kwargs": 300 select, 1000 return, 500 kwargs, seed 5
7. "huge": 8000 select, 10000 return, 100 kwargs, seed 6
8. "distinct-huge": 6000 select, 6000 return, 200 kwargs, seed 7, distinct=True

Hmm, "mostly-null" with 5000 return and 50 select: the loop is 5000 iterations, most NULL. Fine.

Let's check memory: sql for 8000 select cols, each ~ "`allele`.`c123` AS `a123`" ~ 25-30 chars, plus ", " → ~240KB. Fine.

Now, the output string: for huge case, 10000 return columns → select_list ~ 10000 * 30 = 300KB. Fine.

Now let's double check the regex substitution. `re.sub(SELECT_LIST_REGEX, replacement, sql)`. The replacement contains the select_list which may contain backslashes? No. But it may contain `\` from... no. But wait — the replacement string in re.sub interprets backslash escapes! Our select_list contains backticks and letters, no backslashes. Good. But what about the `distinct` group? Fine.

Hmm, but actually the replacement is built with `.format()` — if select_list contained `{` or `}` it would be an issue, but it doesn't.

Wait, there is a subtlety: `re.sub(pattern, repl, string)` — repl is treated as a template where `\g<name>` etc. Our repl has no backslashes. Good.

Now, does the function mutate its arguments? return_columns is iterated, not mutated. kwargs read only. sql read only. So we can reuse the same objects across calls. Good — thunks can return the same objects each time. But to be safe with "same work on every call", the function doesn't mutate, so fine.

Actually wait: `select_info` dict built from parsing. Fine.

Now, one concern: the function's first line `select_info = {...}` uses `_parse_sql_select_named_expression(sql)` which does `re.match(SELECT_LIST_REGEX, sql).group(2)`. Our sql starts with "SELECT ". Good.

Now the `return_column = tuple(return_column)[0]` — our return_columns are 1-tuples like ("a0",). tuple(("a0",))[0] = "a0". Good.

Now checks: small edge inputs.

- ("empty-return", lambda: (SIMPLE_SQL, [])) — runs, output "SELECT  FROM ...". Actually `"SELECT {distinct}{select_list} FROM"` with distinct="" and select_list="" gives "SELECT  FROM". Fine.
- ("single", lambda: ("SELECT `t`.`a` AS `a` FROM `t`", [("a",)]))
- ("distinct", lambda: call("SELECT DISTINCT `t`.`a` AS `a` FROM `t`", [("a",), ("b",)], b=("t", "b")))

These may raise; that's OK, but they should behave identically between original and modified. Fine.

Hmm, actually one risk: if NAMED_EXPRESSION_REGEX differs, checks also fail identically (both raise) so they'd still "pass" the identical behaviour check? Actually if both raise the same, that's identical. But cases must run to completion. So the risk is only for cases.

Let me reduce risk by making the SQL exactly match the function's own output format. The function outputs `` `{table}`.`{column}` AS `{return_column}` `` — so a round-trip: if we feed the output back in, it must parse. So the format is definitely supported. 

Now let me also consider: maybe NAMED_EXPRESSION_REGEX uses `[^`]+` or `\w+`. Our names are alphanumeric. Fine.

Let me now also think: could the regex require the alias to be present and group 4 to be something else? We covered.

One more possibility: NAMED_EXPRESSION_REGEX = r"(?:(`?(\w+)`?)\.)?(`?(\w+)`?)(?:\s+AS\s+(`?(\w+)`?))?" — then group1=table w/backticks, group2=table, group3=column, group4=column, group5=alias. Then [1]=table with backticks, [2]=column with backticks, [4]=alias. Then output would be "``allele``.`c0` AS `a0`". Weird but runs. Our test would still run. Fine.

The only failure mode is if the regex doesn't match at all. Given the format is the function's own output format, it should match.

Hmm, unless NAMED_EXPRESSION_REGEX expects no backticks. But then the function's own output wouldn't round-trip... but the function might never be fed its own output. Hmm. In `harmonize_germline_sql`, the SQL comes from elsewhere. Let me think about what the input SQL looks like.

Actually, let me reconsider. Maybe the SQL uses no backticks? The function adds backticks in output. Hmm.

Let me think about the actual dx-toolkit germline SQL. I recall SQL like:
```
SELECT `allele`.`locus_id` AS `locus_id`, ...
```
Actually I think the SQL is generated by dxpy's extract code which uses backticks (MySQL style). Let me go with backticks.

Hmm, I want to hedge. Could I make the input SQL contain both? No, each named expression must match.

Let me think harder about the real regex. Searching memory: dx-toolkit germline_utils.py... I believe there's:

```python
SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"
NAMED_EXPRESSION_REGEX = r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"
```

I'm fairly confident because the group indices 1,2,4 make sense only with this structure (group1 = full qualified name, group2 = table, group3 = column, group4 = " AS alias" full, group5 = alias).

Wait: `.groups()[1], .groups()[2], .groups()[4]` → group2, group3, group5. So table=group2, column=group3, alias=group5. Yes. And group1 = whole table.column, group4 = " AS alias". That's exactly the pattern above. 

So NAMED_EXPRESSION_REGEX = r"(`?(\w+)`?\.`?(\w+)`?)(\s+AS\s+`?(\w+)`?)?"

Hmm wait, but then in the pattern `(`?(\w+)`?\.`?(\w+)`?)`, group1 is the outer, group2 = first \w+, group3 = second \w+. Yes.

Great. Our format matches.

But note: the `\s+AS\s+` requires whitespace around AS. Our format `` `allele`.`c0` AS `a0` `` has spaces. Good.

Now let me write the code.

Also need: `from dxpy.dx_extract_utils.germline_utils import _harmonize_sql_select_named_expression`? The task says import it as such. But do we need to import it? We only write checks and cases; the runner imports the function. But maybe we should import for... no, we don't call it. Actually we don't need to import at all. But the example imports the module to set globals. Here no globals needed. I'll skip imports of the function, or include for clarity? The instructions say "Import the repository's modules exactly as shown in the task." We don't need it. I'll not import to avoid issues. Actually it's harmless to import. Hmm, but if import fails... it won't. I'll skip.

Actually, we should be careful: nothing needed from the module. Fine.

Let me write the code.

```python
import random

def _build(n_select, n_return, n_kwargs, seed, distinct=False):
    rng = random.Random(seed)
    parts = []
    aliases = []
    for i in range(n_select):
        col = "c%d" % i
        alias = rng.choice(["a%d" % i, col, "alias_%d" % i])
        aliases.append(alias)
        parts.append("`allele`.`%s` AS `%s`" % (col, alias))
    sql = "SELECT " + ("DISTINCT " if distinct else "") + ", ".join(parts) + " FROM `allele` JOIN `ref` ON `allele`.`locus_id` = `ref`.`locus_id`"
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
            name = rng.choice(aliases)
        elif r < 0.75 and kw_names:
            name = rng.choice(kw_names)
        else:
            name = "miss%d" % i
        return_columns.append((name,))
    return sql, return_columns, kwargs
```

Then module-level build the cases data.

```python
_SMALL = _build(100, 150, 5, 0)
...
```

Then cases() returns list of (label, lambda: call(sql, rc, **kw)).

Wait — `call(sql, rc, **kw)` — but the function signature is `(sql, return_columns, **kwargs)`. So `call(sql, return_columns, **kwargs)`. Good.

But careful: if kwargs is empty, `call(sql, rc)`.

Let me write thunks as closures:

```python
def _thunk(sql, rc, kw):
    return lambda: call(sql, rc, **kw)
```

Good.

Now checks:

```python
def checks():
    simple = "SELECT `t`.`a` AS `a` FROM `t`"
    return [
        ("empty-return", lambda: (simple, [])),
        ("single", lambda: (simple, [("a",)])),
        ("distinct-with-kwarg", lambda: call("SELECT DISTINCT `t`.`a` AS `a` FROM `t`", [("a",), ("b",)], b=("t", "b"))),
    ]
```

Wait, "empty-return" — return_columns empty → select_list empty → "SELECT  FROM `t`". Runs fine.

Now, let me double check the `_build` for the distinct case: sql = "SELECT DISTINCT `allele`.`c0` AS `a0`, ... FROM ...". The regex `SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM` — group1 = "DISTINCT ", group2 = select list. Good.

Now the substitution: `"SELECT {distinct}{select_list} FROM".format(distinct="DISTINCT ", select_list=...)`. Good.

Now let's finalize the 8 cases with reasonable sizes.

Let me reconsider performance. The dominant cost for large cases: re.sub over the SQL. Let's estimate re.sub speed ~ 100 MB/s? For an 800KB string with a simple pattern, maybe 5-10ms. Plus the parse: 8000 re.match calls, each maybe 1µs → 8ms. Plus building select_lists: 10000 format operations ~ 5ms. So total maybe 20-30ms. Good.

For the huge case with 8000 select: fine.

Let me maybe push one case bigger to get closer to 200ms: n_select=20000, n_return=25000. SQL ~ 20000*30 = 600KB. Parse 20000 matches ~20ms. Format 25000 ~ 15ms. re.sub ~ 10ms. Total ~50ms. Hmm.

Actually re.match with a compiled-cached pattern on a 30-char string is maybe 0.5µs. 20000 → 10ms.

Let's just do a range and not worry; 4 largest will be kept.

Let me set:
1. small: 100/150/5 seed 0
2. medium: 800/1200/20 seed 1
3. distinct-mid: 600/900/10 seed 2 distinct
4. large: 3000/4000/50 seed 3
5. mostly-null: 60/6000/0 seed 4
6. many-kwargs: 400/1500/800 seed 5
7. huge: 12000/15000/100 seed 6
8. distinct-huge: 9000/12000/300 seed 7 distinct

Total build time: building strings of ~12000*30 = 360KB, fine. All under 10s.

Memory: fine.

Now, one thing: in `_build`, `rng.choice(["a%d" % i, col, "alias_%d" % i])` — for i where col == "a%d"? No, col = "c%d". distinct.

Aliases may collide across i? "a0","c0","alias_0" for i=0; "a1","c1","alias_1" for i=1. No collisions. Good, so select_info has n_select entries.

return_columns: 45% hits on select aliases, 30% kwargs, 25% misses. Good diversity.

Now, `miss%d` names — these are not in select_info nor kwargs → NULL. Good.

Now the output size: for huge case, select_list has 15000 entries, each ~ "`allele`.`c123` AS `a123`" ~ 28 chars → 420KB. Fine.

Wait — for the "mostly-null" case, n_return=6000 with n_select=60 and n_kwargs=0. So 45% of 6000 = 2700 hits (aliases from 60), 30% but kw_names empty → falls to else → miss. So ~3300 NULLs. Fine.

Hmm, careful: `elif r < 0.75 and kw_names:` — if kw_names empty, condition false, goes to else. Good.

Now let me also make sure the SQL doesn't accidentally contain " FROM" inside the select list. Our select list has "`allele`.`c0` AS `a0`" — no " FROM". Good.

Also, the JOIN clause contains " ON ... " — no FROM. Good.

Now, does the function's re.sub replace correctly? The match is "SELECT ... FROM" (the first FROM). Replacement "SELECT {distinct}{select_list} FROM". So the result is the new select list + " FROM `allele` JOIN ...". Good.

Let me write the final code.

One more: the task says thunks return tuples of positional args, or `call(...)` for kwargs. Our thunk returns `call(sql, return_columns, **kwargs)`. Good.

Let me also double-check: is `call` available at module level for use inside lambdas defined at module level? Yes, provided by the harness.

Actually, hmm — for checks I use `call` too. Fine.

Let me write it.

Also consider: should I worry that `**kwargs` with names like "k0" could conflict with the function's parameter names "sql" or "return_columns"? No, "k0" etc. Fine.

Final code:

```python
import random


def _build(n_select, n_return, n_kwargs, seed, distinct=False):
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
            name = rng.choice(aliases)
        elif r < 0.75 and kw_names:
            name = rng.choice(kw_names)
        else:
            name = "miss%d" % i
        return_columns.append((name,))
    return sql, return_columns, kwargs


_CASES = [
    ("small", _build(100, 150, 5, 0, False)),
    ...
]


def _thunk(case):
    sql, rc, kw = case
    return lambda: call(sql, rc, **kw)


def cases():
    return [(label, _thunk(case)) for label, case in _CASES]
```

Wait, `_thunk(case)` — but the lambda captures `sql, rc, kw` from the enclosing function scope. Good.

Hmm, but the label list order. Fine.

Let me write checks and cases.

Actually, one concern about `_build` being called at module level: it uses `random.Random(seed)` — deterministic. Good.

Let me finalize.

Double-check the "empty-return" check: `(simple, [])` → return_columns empty → select_lists empty → select_list "" → re.sub replaces "SELECT `t`.`a` AS `a` FROM" with "SELECT  FROM". Result: "SELECT  FROM `t`". Runs.

Good.

Let me write out.