We need to write inputs for `harmonize_germline_sql(sql)`. It reads a file `return_columns_genotype.json` from `extract_utils_basepath`. Let's inspect what that path is: `from .filter_to_payload import extract_utils_basepath`. We need to figure out the path. It's likely a directory in the repo. Let's check: `src/python/dxpy/dx_extract_utils/filter_to_payload.py` defines `extract_utils_basepath`. Probably `os.path.dirname(__file__)` or similar. The function opens `os.path.join(extract_utils_basepath, "return_columns_genotype.json")`. That file exists in the repo at `src/python/dxpy/dx_extract_utils/return_columns_genotype.json`. So we don't need to create it; it's part of the repo. But we need to import the module, which imports `extract_utils_basepath`. That should work.

We need to generate SQL statements that match the regex `join_condition_regex = r"ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE"`. This is a join on a_id between two tables, followed by WHERE. The function replaces it with join on locus_id. Then it calls `_harmonize_sql_select_named_expression` which uses `SELECT_LIST_REGEX` (defined in the module, not shown but we can infer it matches `SELECT ... FROM`). Let's find `SELECT_LIST_REGEX` definition. It's not in the headers, but it's used. It's likely defined at module level. We don't need to know exactly, but we need to produce SQL that matches. Let's look at the function: `_harmonize_sql_select_named_expression` parses the SELECT list with `_parse_sql_select_named_expression(sql)`. That function isn't shown but we can infer it parses `SELECT ... FROM ...` and extracts table, column, alias. The regex `SELECT_LIST_REGEX` probably matches `SELECT (.*?) FROM`. We need to craft SQL that has a SELECT list with named expressions like `` `table`.`column` AS `alias` ``.

We need to produce realistic SQL from the repository. The caller: `raw_query_api_call(resp, genotype_only_payload)` returns a SQL query string. Then `harmonize_germline_sql` is called on it. So the input is a SQL query string. We need to generate such strings.

Let's look at the JSON file to know what columns are expected. We can read it at module level to generate realistic return columns. Or just use the function's behavior: it reads the JSON, which is a list of return columns (probably a list of strings or lists). The function does `for return_column in return_columns: return_column = tuple(return_column)[0]`. So each element is a list/tuple where first element is the column name. So we can read the actual JSON file to know the columns. But we can also just craft SQL with some columns and let the function add missing ones from the JSON. The function will add NULL for missing columns. To make it do substantial work, we want many return columns (the JSON likely has many). Let's check the file content. We can read it in our code at module level to build SQL that includes some but not all columns, so it has to add many NULLs.

We need 8 cases. Each case is a thunk returning `(sql,)`. The SQL should be a string that matches the regex and has a SELECT list. We need to ensure the regex search finds a match. The regex requires `ON `table`.`a_id` = `table2`.`a_id` WHERE`. So we need a JOIN clause. Let's construct a typical query:

```
SELECT `g`.`a_id` AS `a_id`, `g`.`locus_id` AS `locus_id` FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE ...
```

But the regex is `r"ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE"`. So it looks for `ON `g`.`a_id` = `a`.`a_id` WHERE`. It captures group(1)=g, group(2)=a_id, group(3)=a, group(4)=a_id. Then it replaces with `ON `g`.`locus_id` = `a`.`locus_id` WHERE`. So the original must have `ON `g`.`a_id` = `a`.`a_id` WHERE`. Note: it requires the WHERE immediately after (with whitespace). So the SQL must have that exact pattern.

Also `_harmonize_sql_select_named_expression` uses `SELECT_LIST_REGEX` to match the SELECT list. We need to know what that regex is. Let's search the repo for `SELECT_LIST_REGEX`. It's likely defined in the same file. Since we don't have it, we can infer from usage: `distinct = re.match(SELECT_LIST_REGEX, sql).group(1)` and then `re.sub(SELECT_LIST_REGEX, "SELECT {distinct}{select_list} FROM", sql)`. So `SELECT_LIST_REGEX` matches from `SELECT` up to `FROM`, capturing the distinct part (e.g., `DISTINCT ` or empty). It probably is something like `r"SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM"` but with group(1) being the distinct. Actually group(1) is used as `distinct`, so it's likely `r"SELECT\s+(DISTINCT\s+)?.*?FROM"` with group(1) optional. But we don't need to know exactly; as long as our SQL starts with `SELECT` and has `FROM`, it should match. We can just write standard SQL.

We need to make the function do substantial work. The work is:
- Read JSON file (cached? No, it opens every time. That's I/O, but it's part of the function. We can't avoid that. The file is small probably.)
- Regex search and sub.
- `_harmonize_sql_select_named_expression`: parse SELECT list, iterate over return_columns (from JSON), for each column check if in select_info, else if in kwargs (ref), else NULL. Then join with ", ". Then regex sub.

The heavy part is likely the number of return columns. Let's check the JSON file size. We can read it in our code to see. But we can't run code here. We can guess it's a list of columns for genotype table. Probably around 20-50 columns. That's not huge. To make it more substantial, we can generate SQL with a large SELECT list (many columns) and many joins? But the function only cares about the first join matching the regex. The regex search finds the first occurrence. The rest of the SQL can be large. The `_parse_sql_select_named_expression` parses the SELECT list, so if we have many columns in the SELECT, it will parse them all. That could be heavy. Also the return_columns from JSON is fixed. So the work is proportional to the number of columns in the SELECT list and the number of return columns. We can make the SELECT list huge (e.g., thousands of columns) to stress the parsing. But we must ensure the regex still matches and the function doesn't fail. The `_parse_sql_select_named_expression` probably uses a regex to find all `` `table`.`column` AS `alias` `` patterns. If we provide many such, it will parse them. That could be a good stress.

Also we can vary the number of columns, the number of joins, the presence of DISTINCT, etc.

We need 8 cases. Let's design:

1. Typical small query with a few columns, some from JSON, some not.
2. Large SELECT list with many columns (e.g., 1000 columns) to stress parsing.
3. Query with DISTINCT.
4. Query with many joins (but only one matches the regex? Actually the regex looks for `ON `table`.`a_id` = `table2`.`a_id` WHERE`. If there are multiple joins, the regex search will find the first one that matches. The replacement only replaces that one. So we can have additional joins before or after. The function only replaces the first match. So we can have a complex query with many joins.
5. Query where the SELECT list contains all return columns (so no NULLs added).
6. Query where the SELECT list contains none of the return columns (so all NULLs added).
7. Query with a mix, and the ref column is present (so it uses the kwargs branch). The kwargs is `ref=(allele_table, "a_id")`. So if the return_columns includes "ref", it will use the allele table and a_id. We need to ensure the return_columns JSON contains "ref"? Let's check. The function is called for genotype only queries, and the caller adds `{"ref": "allele$ref"}` to the fields. So the JSON probably includes "ref". So if the SELECT list doesn't have "ref", it will add `NULL AS `ref``? Wait, the code: `elif return_column in kwargs: select_lists.append("`{table}`.`{column}` AS `ref`".format(...))`. So if return_column is "ref", it uses the kwargs. So we need to make sure the JSON contains "ref". We can read the JSON to see. But we can't. We can just assume it does. If it doesn't, that branch won't be taken. But we can still test the other branches.

To be safe, we can read the JSON file at module level and use its content to build SQL that includes some of those columns. That way we know exactly which columns are in return_columns. We can import `extract_utils_basepath` and read the JSON. That's allowed: setup at module level.

Let's write code to read the JSON file and get the list of return columns. Then we can generate SQL that includes a subset of them.

We need to import the function. The import path: `from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql`. We need to make sure the package is importable. The repo is likely installed or we can add to sys.path. The task says "Import the repository's modules exactly as shown in the task." So we just do that.

We also need `WORKDIR` for files? The function reads a file from `extract_utils_basepath`, which is in the repo. It doesn't write anything. So we don't need WORKDIR.

Now, let's design the SQL generator. We need to produce a valid SQL string that matches the regex and has a SELECT list. Let's look at the regex for the join: `r"ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE"`. So the SQL must contain something like:

`... JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE ...`

Note: the table names in the ON clause are captured. The first is `g`, second is `a`. The replacement uses `\1` and `\3`, so it becomes `ON `g`.`locus_id` = `a`.`locus_id` WHERE`. So the table aliases must be word characters. The column must be exactly `a_id` (case-sensitive? The regex uses `a_id` literally, so it must be `a_id`). So we need `a_id` in backticks.

We can generate a query like:

```
SELECT {select_list} FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE `g`.`locus_id` > 0
```

But the regex requires `ON ... WHERE` with whitespace. So we need `ON `g`.`a_id` = `a`.`a_id` WHERE`. That's fine.

The SELECT list should be a comma-separated list of `` `table`.`column` AS `alias` ``. We can generate many such columns. The `_parse_sql_select_named_expression` will parse them. We need to know what it expects. It probably uses a regex like `r"`(\w+)`.`(\w+)` AS `(\w+)`"`. So we can generate columns with table alias `g`, column names like `col1`, `col2`, and alias same as column. Or we can use different aliases.

To make the function do work, we want the number of return columns to be large? The JSON is fixed. Let's read it at module level and see how many there are. We can't run, but we can write code that reads it and uses it. So in our code, we can do:

```python
import json
import os
from dxpy.dx_extract_utils.filter_to_payload import extract_utils_basepath
with open(os.path.join(extract_utils_basepath, "return_columns_genotype.json")) as f:
    _RETURN_COLUMNS = json.load(f)
```

Then we know the list. We can use it to generate SQL that includes some of those columns. For example, we can take the first N columns and include them in the SELECT, so the function has to check each against the parsed select_info. If we include all, it will use the first branch. If we include none, it will use the NULL branch. If we include "ref", it uses the kwargs branch (if "ref" is in the JSON). We can also include columns not in the JSON to make it skip? Actually the function iterates over return_columns from JSON. So the number of iterations is fixed by the JSON size. The work per iteration depends on whether the column is in select_info. The select_info is built from the SQL's SELECT list. So if the SQL has many columns, building select_info is heavier. So we can stress by making the SQL SELECT list huge, regardless of the JSON columns. The function will parse all those columns into select_info, then iterate over the JSON columns (maybe 50) and do dictionary lookups. So the heavy part is parsing the huge SELECT list. So we can generate SQL with thousands of columns in the SELECT list. That will make `_parse_sql_select_named_expression` do a lot of work. We need to ensure it doesn't fail. We can test with moderate numbers.

Also we can make the SQL string itself huge by adding many joins or WHERE conditions. The regex search and sub will scan the whole string. So a large SQL string will make the regex operations slower. We can add many characters after the WHERE clause.

So for cases, we can vary:
- Number of columns in SELECT (small, large).
- Presence of DISTINCT.
- Number of joins (but only one matching the regex).
- Length of WHERE clause.
- Whether the SELECT list contains all, some, or none of the return columns.
- Whether it contains "ref".

We need 8 cases. Let's outline:

1. `typical`: small query, ~10 columns, includes some return columns, no DISTINCT.
2. `large-select`: 2000 columns in SELECT, includes a few return columns.
3. `distinct`: same as typical but with `SELECT DISTINCT`.
4. `all-return-columns`: SELECT list includes all columns from the JSON (so no NULLs added). We can generate this by reading the JSON and using those columns as aliases.
5. `no-return-columns`: SELECT list includes columns not in the JSON (so all NULLs added).
6. `ref-present`: SELECT list includes "ref" (if it's in the JSON) or we just include a column named "ref" and see. Actually the function checks `if return_column in select_info` first. If "ref" is in select_info, it uses that. If not, it checks `elif return_column in kwargs`. So if the JSON contains "ref", and we don't put "ref" in the SELECT, it will use the kwargs branch. So we can have a case where the SELECT doesn't have "ref", so it uses the allele table. That tests the kwargs branch. We can also have a case where the SELECT has "ref", so it uses the first branch. So two cases.
7. `many-joins`: a query with many joins, but the first matching regex is somewhere in the middle. The regex search will find the first match. We can put the matching join later, so it has to scan through many joins. This tests the regex search on a large string.
8. `long-where`: a query with a very long WHERE clause (e.g., 100,000 characters) to stress the regex sub.

We need to ensure each call takes roughly 1 ms to 200 ms. 2000 columns might be too fast? Let's estimate: parsing 2000 columns with regex might take a few ms. To get up to 200 ms, we might need larger. But we don't want to exceed 1 s. We can try 10,000 columns. But building the SQL string at module level is fine. The thunk just returns the string. The function will parse it. Let's be careful: the function reads the JSON file every call. That's I/O. It might be cached by OS, but still. The file is probably small. So that's a constant overhead.

We can also make the SQL string very long (e.g., 1 MB) by adding a long WHERE clause. The regex search will scan the whole string. That could be slow. But we need to ensure the regex matches. The regex is `ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE`. It searches for the pattern. If we put the pattern at the beginning, the search is fast. If we put it at the end of a 1 MB string, the search has to scan the whole string. That could be a good stress. We can put a lot of comments or conditions before the ON clause. But the SQL must be valid? The function doesn't validate SQL, it just does regex. So we can put arbitrary text before the ON clause as long as it doesn't contain the pattern. So we can prepend a large string of random characters or spaces. But we must ensure the regex doesn't match earlier. We can just put a long string of `x` characters. That's fine.

However, we need to be careful: the function also does `re.sub` on the whole string. So a large string will make both search and sub slower.

Let's design the cases with varying sizes.

First, let's write a helper to build a SQL query.

We need to import the function and the basepath. Let's write module-level code to read the JSON and get the list of return columns. We'll call it `_RETURN_COLUMNS`. We need to handle the format: it's a list of lists? The function does `tuple(return_column)[0]`, so each element is a list/tuple. So `_RETURN_COLUMNS` is a list of lists. We can extract the first element of each: `[rc[0] for rc in _RETURN_COLUMNS]`. Let's call it `_COLUMN_NAMES`.

Now, we can generate SQL SELECT lists. We need to know the exact format of the SELECT list that `_parse_sql_select_named_expression` expects. Let's infer from the function: it returns a list of tuples `(table, column, alias)`. So the SQL must have `` `table`.`column` AS `alias` ``. We can generate columns like `` `g`.`col{i}` AS `col{i}` ``. The table alias can be `g` (genotype). The column names can be anything. The aliases can be the same as column names or different. The function uses the alias to match against return_column. So if we want a return column to be found, the alias must match the return column name. So for the "all-return-columns" case, we can generate columns with aliases exactly equal to the return column names. For the "no-return-columns" case, we can use aliases that are not in the return columns (e.g., `col1`, `col2`). For the "ref-present" case, we include an alias `ref` if it's in the return columns. We can check if `"ref"` is in `_COLUMN_NAMES`. If not, we can still include it, but it won't trigger the kwargs branch because the loop is over `_RETURN_COLUMNS`. So we need to know if "ref" is in the JSON. Let's read the JSON at module level and check. If it's not, we can't test the kwargs branch. But the caller adds `{"ref": "allele$ref"}` to the fields, so the JSON likely includes "ref". We'll assume it does. We can write code that conditionally includes it.

Now, let's write the SQL builder.

```python
def _make_sql(select_columns, distinct=False, pre_text="", post_text="", where_text="1=1"):
    distinct_str = "DISTINCT " if distinct else ""
    select_list = ", ".join(select_columns)
    sql = f"SELECT {distinct_str}{select_list} FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE {where_text}"
    return pre_text + sql + post_text
```

Wait, the regex requires `ON `g`.`a_id` = `a`.`a_id` WHERE`. So the WHERE must immediately follow with whitespace. In our builder, we have `WHERE {where_text}`. That's fine: `WHERE` followed by space and then where_text. The regex looks for `ON ... WHERE` with `\s+` before WHERE. So `ON `g`.`a_id` = `a`.`a_id` WHERE` matches. Good.

But note: the regex captures the table aliases. It expects `ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE`. So the first table alias is `g`, second is `a`. That's fine.

Now, for the SELECT list, we need to generate columns. The `_parse_sql_select_named_expression` probably uses a regex to find all `` `table`.`column` AS `alias` ``. We should ensure our columns match that. Let's use exactly that format.

We can generate columns with table alias `g` and column names like `col{i}` and alias `col{i}`. Or we can use different aliases. For the "all-return-columns" case, we use the actual return column names as aliases.

Let's write a function to generate a list of column expressions:

```python
def _col_expr(table, column, alias=None):
    if alias is None:
        alias = column
    return f"`{table}`.`{column}` AS `{alias}`"
```

Now, cases:

1. `typical`: small SELECT list with 10 columns, some aliases matching return columns. We can pick a few from `_COLUMN_NAMES` and some random ones. Let's take the first 5 return columns and 5 random ones. No DISTINCT.

2. `large-select`: 5000 columns, all with random aliases (not in return columns). This stresses parsing.

3. `distinct`: same as typical but with DISTINCT.

4. `all-return-columns`: SELECT list includes all return columns as aliases. The number of return columns might be around 50. So this is small. But it tests the branch where all are found. To make it heavier, we can also add many extra columns with random aliases. So the SELECT list is large, but includes all return columns. Let's make it 2000 columns total, where the first N are the return columns, and the rest are random.

5. `no-return-columns`: SELECT list has 2000 columns, none of which match return columns. So all return columns will be added as NULL. This tests the NULL branch heavily.

6. `ref-present`: We need to know if "ref" is in `_COLUMN_NAMES`. If yes, we can create a SELECT list that does NOT include "ref", so the function will use the kwargs branch for "ref". We can make this case have a moderate SELECT list (e.g., 1000 columns) and ensure "ref" is not among the aliases. This tests the kwargs branch. If "ref" is not in the JSON, we can skip this and replace with another case. But we can check at module level.

7. `many-joins`: A query with many joins before the matching join. The regex search will scan. We can build a SQL with a long chain of joins. For example, `SELECT ... FROM table1 JOIN table2 ON ... JOIN table3 ON ... ... JOIN allele AS a ON `g`.`a_id` = `a`.`a_id` WHERE ...`. The regex will find the first `ON `g`.`a_id` = `a`.`a_id` WHERE`. We need to ensure no earlier join matches the pattern. We can use different column names in earlier joins (e.g., `b_id` instead of `a_id`). So we can have 1000 joins with `ON `t1`.`b_id` = `t2`.`b_id``. Then finally the matching join. The SQL string will be large (maybe 100 KB). The regex search will scan it all. This is a good stress.

8. `long-where`: A query with a very long WHERE clause. We can put the matching join at the beginning, then a huge WHERE clause (e.g., 500,000 characters of `x`). The regex search will match early, but the `re.sub` will process the whole string. Actually `re.sub` with the pattern will scan the whole string to find all matches. Since there's only one match, it will still scan the whole string. So a long WHERE clause will make `re.sub` slower. We can also make the SELECT list large. Let's make a case with a 1 MB SQL string. But we must be careful: the function also reads the JSON and does other stuff. 1 MB string is fine. The regex operations on 1 MB should take some milliseconds.

We need to ensure each call takes between 1 ms and 200 ms. We can adjust sizes. Since we can't run, we'll pick moderate sizes that are likely in range. For example, 5000 columns might take a few ms. 1000 joins might take a few ms. A 1 MB string might take ~10 ms. To be safe, we can make some cases larger, like 20000 columns, or 5000 joins, or 5 MB string. But we don't want to exceed 1 s. Let's estimate: Python regex on a 5 MB string is quite fast, maybe 50 ms. Parsing 20000 columns with a regex might be slower. Let's be conservative and use sizes that are likely under 200 ms. We can also note that the function reads the JSON file every call, which might add overhead. But that's constant.

We can also make the SQL string have many characters by adding a long comment at the beginning. But comments might not be valid SQL, but the function doesn't care. We can just prepend a long string of spaces or 'x'. However, the regex search might be optimized. It's fine.

Let's write the code. We need to import `random` for generating random column names? We can just use deterministic generation with a seed. The task says use a fixed random seed (`random.Random(0)`) when generating data. We'll do that.

We need to build all inputs at module level or in the thunk. Since the thunks just return the SQL string, we can build the SQL strings at module level and have the thunk return them. That's efficient. The function doesn't modify the SQL string (strings are immutable), so we can reuse the same string across calls. But wait: the function does `sql = re.sub(...)` and then `sql = _harmonize_sql_select_named_expression(...)`. It doesn't modify the original string in place (strings are immutable). So we can safely reuse the same string. The thunk can just return `(sql,)`.

However, the function reads the JSON file every call. That's fine.

Let's write the code.

First, imports:

```python
import json
import os
import random
from dxpy.dx_extract_utils.filter_to_payload import extract_utils_basepath
from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql
```

Wait, the import path: the task says `from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql`. So we do that.

We need to read the JSON file. We can use `extract_utils_basepath` to get the directory. Let's do:

```python
_JSON_PATH = os.path.join(extract_utils_basepath, "return_columns_genotype.json")
with open(_JSON_PATH) as f:
    _RETURN_COLUMNS_RAW = json.load(f)
_RETURN_COLUMNS = [tuple(rc)[0] for rc in _RETURN_COLUMNS_RAW]
```

Now, we need to know if "ref" is in `_RETURN_COLUMNS`. We can check.

Now, let's write a helper to build a SQL query.

```python
def _build_sql(select_exprs, distinct=False, pre="", post="", where="1=1"):
    distinct_str = "DISTINCT " if distinct else ""
    select_list = ", ".join(select_exprs)
    sql = f"SELECT {distinct_str}{select_list} FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE {where}"
    return pre + sql + post
```

We need to generate select expressions. A select expression is `` `g`.`col{i}` AS `alias{i}` ``. We can use a function:

```python
def _col_expr(i, alias=None):
    if alias is None:
        alias = f"col{i}"
    return f"`g`.`col{i}` AS `{alias}`"
```

Now, generate cases.

Case 1: typical. Let's take 5 return columns and 5 random columns. We'll use the first 5 from `_RETURN_COLUMNS` as aliases. But we need to ensure the column names are valid. We can just use the return column names as both column and alias? Actually the expression is `` `g`.`{col}` AS `{col}` ``. So we can use the return column name as the column name and alias. That's fine.

```python
rng = random.Random(0)
typical_cols = []
for i, rc in enumerate(_RETURN_COLUMNS[:5]):
    typical_cols.append(_col_expr(i, alias=rc))
for i in range(5):
    typical_cols.append(_col_expr(100+i, alias=f"extra{i}"))
typical_sql = _build_sql(typical_cols)
```

Case 2: large-select. 5000 columns with random aliases not in return columns. We can generate aliases like `f"x{i}"`. To ensure they are not in return columns, we can prefix with "x". But we should check that none of the return columns start with "x"? Not necessary, but to be safe, we can just use a prefix that's unlikely. Or we can just use random strings. But the function only cares about exact match. So as long as the alias is not exactly equal to any return column, it's fine. We can generate aliases like `f"col{i}"` and hope none are in return columns. But some return columns might be named "col1"? Unlikely. To be safe, we can check against `_RETURN_COLUMNS` and if collision, append "_x". But we can just use a prefix like "extra_". Let's do that.

```python
large_cols = []
for i in range(5000):
    large_cols.append(_col_expr(i, alias=f"extra_{i}"))
large_sql = _build_sql(large_cols)
```

Case 3: distinct. Same as typical but with distinct=True.

Case 4: all-return-columns. Include all return columns as aliases, plus many extras. Let's say 2000 columns total. The first len(_RETURN_COLUMNS) are the return columns, the rest are extras.

```python
all_ret_cols = []
for i, rc in enumerate(_RETURN_COLUMNS):
    all_ret_cols.append(_col_expr(i, alias=rc))
for i in range(2000 - len(_RETURN_COLUMNS)):
    all_ret_cols.append(_col_expr(1000+i, alias=f"extra_{i}"))
all_ret_sql = _build_sql(all_ret_cols)
```

Case 5: no-return-columns. 2000 columns, all extras. Ensure none match return columns. Use prefix "none_".

```python
no_ret_cols = [_col_expr(i, alias=f"none_{i}") for i in range(2000)]
no_ret_sql = _build_sql(no_ret_cols)
```

Case 6: ref-present. We need to know if "ref" is in `_RETURN_COLUMNS`. If yes, we create a SQL that does NOT include "ref" in the SELECT list, so the function will use the kwargs branch. We can have 1000 columns, all extras, and ensure "ref" is not among them. Since we use prefix "extra_", "ref" won't be there. So this is similar to no-return-columns but with a different size. Actually, to specifically test the kwargs branch, we just need a case where "ref" is in `_RETURN_COLUMNS` and not in the SELECT. The function will iterate over all return columns; for "ref", it will go to the `elif return_column in kwargs` branch. So any case that doesn't include "ref" will test that branch. So we can just use a moderate size. Let's make it 1000 columns.

```python
ref_cols = [_col_expr(i, alias=f"extra_{i}") for i in range(1000)]
ref_sql = _build_sql(ref_cols)
```

But wait: if "ref" is not in `_RETURN_COLUMNS`, this case won't test that branch. We can check at module level and if not, we can still include it but it won't matter. We'll just include it.

Case 7: many-joins. We want a SQL string with many joins before the matching join. Let's build a query with 1000 joins. The first join will be the matching one? No, we want the matching join to be at the end. So we build a chain: `FROM table0 JOIN table1 ON `t0`.`b_id` = `t1`.`b_id` JOIN table2 ON `t1`.`b_id` = `t2`.`b_id` ... JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE ...`. But we need the genotype table to be `g`? The regex captures the first table alias in the ON clause. It doesn't care about the FROM. So we can just have a long chain of joins, and then finally the matching join. The regex search will scan the whole string. To make it heavy, we can make the joins have long table names and column names. Let's generate 2000 joins. Each join adds about 50 characters. That's 100 KB. The regex search will scan it. That should be fine.

We need to ensure the pattern `ON `g`.`a_id` = `a`.`a_id` WHERE` appears only at the end. So we can use different column names for earlier joins. Let's use `b_id` for all earlier joins. The table aliases can be `t0`, `t1`, etc. The ON clause: `ON `t0`.`b_id` = `t1`.`b_id``. That doesn't match the regex because the column is `b_id`, not `a_id`. So the regex will skip them.

Let's build:

```python
def _build_many_joins_sql(num_joins):
    select_list = ", ".join([f"`t0`.`col{i}` AS `col{i}`" for i in range(10)])
    sql = f"SELECT {select_list} FROM `table0` AS `t0`"
    for i in range(1, num_joins):
        sql += f" JOIN `table{i}` AS `t{i}` ON `t{i-1}`.`b_id` = `t{i}`.`b_id`"
    # finally the matching join
    sql += " JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE 1=1"
    return sql
```

Wait, the matching join uses `g` and `a`. But we haven't defined `g` in the FROM. That's fine; the regex just looks for the pattern. The function will replace it with `ON `g`.`locus_id` = `a`.`locus_id` WHERE`. It doesn't care if `g` is defined. So it's fine.

We can set num_joins = 2000.

Case 8: long-where. We want a very long WHERE clause. We can build a normal query and then append a long string to the WHERE clause. For example, `WHERE `g`.`col1` = '...'` with a long string. Or just `WHERE 1=1` followed by a long comment? The function doesn't parse the WHERE, so we can just put a long string of `x` characters. But we need to ensure the regex matches. The regex looks for `ON ... WHERE`. So the WHERE must be immediately after the ON clause. So we can do:

`SELECT ... FROM ... ON `g`.`a_id` = `a`.`a_id` WHERE ` + "x"*500000

But wait, the regex is `ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE`. It matches up to `WHERE`. The rest doesn't matter. So we can just append a huge string after `WHERE`. The `re.sub` will process the whole string. So this will make `re.sub` slower. Let's make the total SQL string about 1 MB. We can do `WHERE ` + "x"*1_000_000. That's 1 MB. The regex search will find the match early, but `re.sub` will scan the whole string. That should take some ms.

We can also make the SELECT list large. Let's make a case with 2000 columns and a 500,000 character WHERE clause.

```python
long_where_cols = [_col_expr(i, alias=f"extra_{i}") for i in range(2000)]
long_where_sql = _build_sql(long_where_cols, where="x"*500_000)
```

That's 8 cases. We need exactly 8 measured inputs. We have 8.

Now, checks(): 2 or 3 small edge inputs. These are not measured, just checked for identical behavior. They may raise. We can include:
- empty string: `""` -> regex search will fail (AttributeError: 'NoneType' object has no attribute 'group'). That's fine, it raises. But the task says "These may raise." So it's okay.
- SQL without the join condition: e.g., `"SELECT * FROM genotype"` -> `re.search` returns None, raises AttributeError.
- SQL with the join condition but no SELECT? Actually the function expects a SELECT. If we give a string with the join condition but no SELECT, `_harmonize_sql_select_named_expression` will fail at `re.match(SELECT_LIST_REGEX, sql)`. So that's an edge case.

Let's provide:

```python
def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-join", lambda: ("SELECT * FROM genotype",)),
        ("join-no-select", lambda: ("ON `g`.`a_id` = `a`.`a_id` WHERE 1=1",)),
    ]
```

But wait, the function takes `sql` as a positional argument. So the thunk returns `(sql,)`. That's correct.

Now, we need to ensure that the module-level code doesn't fail. We need to import `extract_utils_basepath`. That might require the package to be installed. The task says we can import as shown. So it should work.

Let's double-check the regex. The regex is `r"ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE"`. Note the backticks. In our SQL, we have `ON `g`.`a_id` = `a`.`a_id` WHERE`. That matches: `ON` followed by space, then backtick, `g`, backtick, dot, backtick, `a_id`, backtick, space, `=`, space, backtick, `a`, backtick, dot, backtick, `a_id`, backtick, space, `WHERE`. Yes.

The replacement is `"ON `\\1`.`locus_id` = `\\3`.`locus_id` WHERE"`. So it replaces with `ON `g`.`locus_id` = `a`.`locus_id` WHERE`. That's fine.

Now, `_harmonize_sql_select_named_expression` uses `SELECT_LIST_REGEX`. We don't know it, but our SQL starts with `SELECT` and has `FROM`. It should match. Let's assume it's something like `r"SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM"`. Our SQL has `SELECT ... FROM`. So it should work.

One potential issue: `_parse_sql_select_named_expression` might expect a specific format. Let's think about what it might do. It probably uses a regex to find all `` `table`.`column` AS `alias` ``. Our expressions are exactly that. So it should parse them.

We need to ensure that the SQL string doesn't contain any characters that would break the regex. For example, if we use `extra_{i}` as alias, that's fine because `\w+` matches word characters. The alias is in backticks, so it's fine.

Now, let's write the full code.

We'll put everything in a single Python block.

We need to import `random` and use `random.Random(0)` for generating data. We'll use it to shuffle or generate random column names? We don't really need randomness, but the task says "use a fixed random seed when generating data". We can use it to generate random column names or just to satisfy the requirement. We can generate random strings for aliases. But deterministic is fine. We'll use `rng = random.Random(0)` and maybe generate random column names for some cases. But our current generation is deterministic without randomness. To comply, we can use `rng` to generate random suffixes. Let's do that for the extra columns.

For example, in `large_cols`, we can use `rng.randint(0, 10**6)` to generate a random number for the alias. But then we need to ensure they don't collide with return columns. Since return columns are specific, random numbers are unlikely to collide. We can do:

```python
large_cols = [_col_expr(i, alias=f"extra_{rng.randint(0, 10**9)}") for i in range(5000)]
```

That uses the seed. Similarly for others.

But we also need to ensure that the aliases are valid for the regex. They are just strings in backticks, so any word characters are fine. `extra_123` is fine.

Let's write the code.

We need to be careful: the function reads the JSON file every call. The JSON file is in the repo. We don't need to create it. But we do read it at module level to get the return columns. That's fine.

Let's write the module-level code.

```python
import json
import os
import random
from dxpy.dx_extract_utils.filter_to_payload import extract_utils_basepath
from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql

# Read the return columns JSON to know which columns the function will add
_JSON_PATH = os.path.join(extract_utils_basepath, "return_columns_genotype.json")
with open(_JSON_PATH) as f:
    _RETURN_COLUMNS_RAW = json.load(f)
_RETURN_COLUMNS = [tuple(rc)[0] for rc in _RETURN_COLUMNS_RAW]

# Helper to build a column expression
def _col_expr(table, column, alias=None):
    if alias is None:
        alias = column
    return f"`{table}`.`{column}` AS `{alias}`"

# Helper to build SQL
def _build_sql(select_exprs, distinct=False, pre="", post="", where="1=1"):
    distinct_str = "DISTINCT " if distinct else ""
    select_list = ", ".join(select_exprs)
    sql = f"SELECT {distinct_str}{select_list} FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE {where}"
    return pre + sql + post

# Generate the SQL inputs at module level
rng = random.Random(0)

# Case 1: typical small query
_typical_cols = []
for i, rc in enumerate(_RETURN_COLUMNS[:5]):
    _typical_cols.append(_col_expr("g", f"col{i}", alias=rc))
for i in range(5):
    _typical_cols.append(_col_expr("g", f"col{100+i}", alias=f"extra_{rng.randint(0, 10**6)}"))
_typical_sql = _build_sql(_typical_cols)

# Case 2: large select list
_large_cols = [_col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}") for i in range(5000)]
_large_sql = _build_sql(_large_cols)

# Case 3: distinct
_distinct_sql = _build_sql(_typical_cols, distinct=True)

# Case 4: all return columns present
_all_ret_cols = []
for i, rc in enumerate(_RETURN_COLUMNS):
    _all_ret_cols.append(_col_expr("g", f"col{i}", alias=rc))
for i in range(2000 - len(_RETURN_COLUMNS)):
    _all_ret_cols.append(_col_expr("g", f"col{1000+i}", alias=f"extra_{rng.randint(0, 10**9)}"))
_all_ret_sql = _build_sql(_all_ret_cols)

# Case 5: no return columns present
_no_ret_cols = [_col_expr("g", f"col{i}", alias=f"none_{rng.randint(0, 10**9)}") for i in range(2000)]
_no_ret_sql = _build_sql(_no_ret_cols)

# Case 6: ref present (tests kwargs branch if "ref" is in return columns)
_ref_cols = [_col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}") for i in range(1000)]
_ref_sql = _build_sql(_ref_cols)

# Case 7: many joins
def _build_many_joins_sql(num_joins):
    select_list = ", ".join([f"`t0`.`col{i}` AS `col{i}`" for i in range(10)])
    sql = f"SELECT {select_list} FROM `table0` AS `t0`"
    for i in range(1, num_joins):
        sql += f" JOIN `table{i}` AS `t{i}` ON `t{i-1}`.`b_id` = `t{i}`.`b_id`"
    sql += " JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE 1=1"
    return sql
_many_joins_sql = _build_many_joins_sql(2000)

# Case 8: long where clause
_long_where_cols = [_col_expr("g", f"col{i}", alias=f"extra_{rng.randint(0, 10**9)}") for i in range(2000)]
_long_where_sql = _build_sql(_long_where_cols, where="x" * 500_000)


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
```

Wait, the task says "exactly 8 measured inputs" for `cases()`. We have 8. Good.

But we need to ensure that the function doesn't modify the SQL string in a way that affects subsequent calls. Since strings are immutable, it's fine. The function returns a new string. The thunk returns the same original string every time. That's fine.

However, the function reads the JSON file every call. That's I/O. It might be slow if the file is large, but it's probably small. We can't avoid that.

Now, we need to check if the SQL we generate actually matches the regex. Let's test mentally for `_typical_sql`:

`SELECT `g`.`col0` AS `a_id`, ... FROM `genotype` AS `g` JOIN `allele` AS `a` ON `g`.`a_id` = `a`.`a_id` WHERE 1=1`

The regex search: `ON\s+`(\w+)`\.`(a_id)`\s+=\s+`(\w+)`\.`(a_id)`\s+WHERE`. It will find `ON `g`.`a_id` = `a`.`a_id` WHERE`. Yes.

The `_harmonize_sql_select_named_expression` will parse the SELECT list. It expects `` `table`.`column` AS `alias` ``. Our expressions are exactly that. So it should work.

One potential issue: the `_parse_sql_select_named_expression` might use a regex that requires no spaces? We have spaces around `AS`. That's standard. It should be fine.

Another potential issue: the `SELECT_LIST_REGEX` might be something like `r"SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM"`. Our SQL has `SELECT ... FROM`. It should match. The `distinct` group will be empty for non-distinct, and "DISTINCT " for distinct. That's fine.

Now, what about the `many-joins` case? The SQL starts with `SELECT ... FROM `table0` AS `t0` JOIN ...`. The regex search will scan until it finds `ON `g`.`a_id` = `a`.`a_id` WHERE`. That appears at the end. So it will scan the whole string. The `re.sub` will replace that one occurrence. The rest of the string remains. Then `_harmonize_sql_select_named_expression` will parse the SELECT list. The SELECT list has only 10 columns. So the parsing is fast. The heavy part is the regex search on the long string. That's good.

What about the `long-where` case? The SQL has a huge WHERE clause. The regex search will find the match early (since the ON clause is before the WHERE). Actually, the regex looks for `ON ... WHERE`. The WHERE is the start of the long string. So the match includes the `WHERE` keyword and then the rest? No, the regex ends at `WHERE`. It doesn't consume the rest. So the match is just `ON `g`.`a_id` = `a`.`a_id` WHERE`. The `re.sub` will replace that match. Then the rest of the string (the huge WHERE clause) remains. But `re.sub` still has to scan the entire string to find all matches. Since there's only one match, it will scan the whole string. So the long WHERE clause makes `re.sub` slower. That's good.

Now, we need to ensure that the inputs don't exceed the limits. The SQL strings are stored in memory. The largest is `long-where` with 500,000 characters plus 2000 columns. That's about 500 KB. The `many-joins` with 2000 joins: each join is about 50 characters, so 100 KB. The `large-select` with 5000 columns: each column is about 30 characters, so 150 KB. All well under 100 MB. The number of values returned by the function is a string, which is under 100,000 values? The output is a single string. That's fine.

The arguments are rendered before and after each call to see if they changed. The argument is a string. It doesn't change. So that's fine.

Now, we need to make sure that the function can run without raising. The only potential issue is if the JSON file doesn't exist or the import fails. But the task says the repository has it. We'll assume it's there.

Let's double-check the import path. The task says: `from dxpy.dx_extract_utils.germline_utils import harmonize_germline_sql`. So we do that. We also import `extract_utils_basepath` from `dxpy.dx_extract_utils.filter_to_payload`. That's used in the function's module. So it should be available.

One more thing: the function uses `extract_utils_basepath` which is imported in its module. We don't need to set it; it's already set. We just read the JSON file using the same path. That's fine.

Now, let's consider if we need to use `WORKDIR`. The function doesn't read or write files in WORKDIR. It reads from the repo. So we don't need WORKDIR.

I think the code is complete.

Let's write the final answer.
