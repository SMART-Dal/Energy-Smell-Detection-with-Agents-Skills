Let me write the code. The function format_table takes a table (list of lists), column_names, column_specs, max_col_width, report_dimensions.

We need 8 cases. Build realistic tables. Let me generate data.

Note: format_table calls len(list(table)[0]) if len(table) > 0. If table is a generator, len(table) fails. Actually repository passes .values() (dict values, which is a view with len). Let's pass lists.

Cases: various sizes, column specs, max_col_width, report_dimensions, unicode strings, long strings, etc.

Let me write.

Note col_widths[i] indexing: if column_specs given, col_widths = [0]*(len(column_specs)+1) but only if table empty. If table non-empty, col_widths = [0]*len(table[0]). With column_specs, column_names becomes ['Row'] + names, so there are len(specs)+1 names. So table rows must have len(specs)+1 columns... Actually if table non-empty with column_specs, col_widths length = len(table[0]) which should match. Fine.

Let's make cases:

1. typical: 50 rows x 8 cols of strings/ints, column_names.
2. large: 2000 rows x 10 cols.
3. wide columns: strings with unicode escapes and long values.
4. column_specs with types.
5. report_dimensions=True.
6. max_col_width small (e.g., 10) forcing truncation.
7. many rows with varying widths, duplicates.
8. empty table with column_names.

Need to be careful about output size < 100000 values. The output is a string; fine. 2000 rows x 10 cols -> string of maybe 2000*10*32 = 640k chars but it's one string value. "keep what it returns under about 100 000 values" — a string is one value. Fine. But time: 2000 rows * 10 cols should be fast, maybe few ms. Let's do up to 5000 rows for stress.

Actually each call should take ~1ms-200ms. format_table is fast; 5000 rows x 10 cols maybe ~20ms. Good.

Let me build data with random seed.

For column_specs case: column_specs is list of dicts with 'name' and 'type'. column_names ignored then. Table rows include the Row column as first element.

Let me write module-level builders.

Potential issue: escape_unicode_string handles control chars. Include some.

Let me write:

```python
import random
from dxpy.utils.pretty_print import format_table

def _table(nrows, ncols, seed, max_len=20, unicode_frac=0.0):
    rng = random.Random(seed)
    rows = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            k = rng.random()
            if k < unicode_frac:
                row.append("".join(rng.choice("abc\n\t\\\x01é") for _ in range(rng.randint(1, max_len))))
            elif k < 0.5:
                row.append(rng.randint(-10**9, 10**9))
            elif k < 0.8:
                row.append(round(rng.uniform(-1e6, 1e6), 4))
            else:
                row.append("".join(rng.choice("abcdefghij") for _ in range(rng.randint(1, max_len))))
        rows.append(row)
    return rows
```

Hmm, mixing types is fine since str() applied.

Wait, \x01 in a string literal is fine, but escape_unicode_string turns it into REPLACEMENT_TABLE entry. Fine.

Let me check REPLACEMENT_TABLE exists — yes used in escape_unicode_string. It's defined in module presumably (headers don't show it but it's used). Fine.

Cases:

1. typical: 100 rows, 8 cols, seed 0, column_names = ["col%d"%i for i in range(8)].
2. large: 4000 rows, 12 cols, seed 1, column_names.
3. unicode-heavy: 500 rows, 6 cols, unicode_frac=0.7, seed 2, column_names with long names.
4. truncation: max_col_width=8, 800 rows, 10 cols, seed 3, column_names.
5. column_specs: 300 rows, 5 data cols + Row, seed 4, column_specs with types.
6. report_dimensions: 1000 rows, 7 cols, seed 5, report_dimensions=True.
7. no column names: 2000 rows, 9 cols, seed 6, no column_names.
8. empty table with column_names: [] with column_names — but that's more of a check. Need 8 measured cases that do work. Let's make case 8: many rows with duplicates and varying widths, seed 7, column_names including a very long name (>32) to trigger truncation of names.

Actually the "empty" case would be edge check. Let's make case 8 realistic: 3000 rows x 6 cols, seed 7.

Hmm but must be diverse. Fine.

checks: empty table no args -> format_table([]) returns border with no columns? Let's see: len(table)==0, column_specs None, column_names None -> col_widths remains undefined... Actually col_widths is only assigned inside if branches. If all None and empty, col_widths not defined -> NameError at border line. So format_table([]) raises. That's fine for checks (may raise). But better to have checks that behave identically. Since both original and modified run same, raising is fine.

checks:
- ("empty", lambda: ([],)) -> raises NameError probably. That's allowed.
- ("single", lambda: ([["a"]],))
- ("none-values", lambda: ([[None, 1], [2, None]],)) with column_names.

Actually None -> str(None) = "None". Fine.

Let me make checks:
1. empty table with column_names: ([], ["A","B"]) — this works: col_widths = [0,0], my_column_names built, formatted_table border... rows none. Works.
2. single row: ([["x"]],)
3. none and odd types: ([[None, 1.5, True],]), column_names maybe.

Let me finalize.

For column_specs case, need types valid: 'float','integer','string','boolean'. col_head uses type_colormap[column_specs[i]['type']].

column_specs = [{'name': 'A', 'type': 'integer'}, ...]. Table rows must have len = len(specs)+1 columns. And col_widths = [0]*len(table[0]) if table non-empty. Good.

Let me write the code.

For case 5: 300 rows, specs 5 -> rows of 6 values. First value is "Row" (float type). Let's generate numbers.

I'll just build table with _table(300, 6, 4).

column_specs = [{'name': f'col{i}', 'type': t} for i, t in enumerate(['integer','float','string','boolean','uint32'])]

Good.

Now write final.

Also note the function does `col_widths[i] = max(...)` for each i in row; if row longer than col_widths -> IndexError. So rows must be uniform length. _table ensures uniform.

For case with column_names length != ncols: col_widths length = ncols (from table[0]). Then loop over column_names sets col_widths[i] — if len(column_names) > ncols -> IndexError. So ensure equal.

Case 3 column_names with long names: ncols=6, names length 6, one long > 32.

Let me write it.

Time estimate: 4000x12 = 48k cells, str + escape each. escape_unicode_string uses regex sub per cell. 48k regex subs ~ maybe 30ms. Fine.

Let me be careful not to exceed 200ms. 4000 rows fine.

Write.