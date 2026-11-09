import ast, json, textwrap, re
ROOT = '/home/javad/energy-run/dx-toolkit/'
OUT = ROOT + 'submissions.jsonl'

def func_src(path, qualname):
    src = open(ROOT + path).read()
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    body, node = tree.body, None
    for part in qualname.split('.'):
        node = next(n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
        body = node.body
    start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
    return ''.join(lines[start:node.end_lineno])

def apply(text, pairs):
    for old, new in pairs:
        assert text.count(old) == 1, ('not found once', old[:80], text.count(old))
        text = text.replace(old, new)
    return text

subs = []

def add(sid, rc, path, qual, pairs, evidence, notes):
    text = apply(func_src(path, qual), pairs)
    if '.' in qual:
        text = textwrap.dedent(text)
    subs.append({"id": sid, "root_cause": rc, "unit": f"{path}::{qual}",
                 "changed": {f"{path}::{qual}": text},
                 "sole_caller_evidence": evidence, "notes": notes})

# 1. _find: extra page request after the limit is reached
add("C3S5-find-extra-page", "C3.S5", "src/python/dxpy/bindings/search.py", "_find", [(
'''        # set up next query
        if resp["next"] is not None:
            query["starting"] = resp["next"]
            query["limit"] = min(query["limit"]*2, 1000)
        else:
            return
''',
'''        # set up next query
        if resp["next"] is not None:
            query["starting"] = resp["next"]
            query["limit"] = min(query["limit"]*2, 1000)
            if num_results == limit:
                return
        else:
            return
''')],
"grep of src/python: _find is called from search.py lines 270, 426, 540, 636, 1023 and the org variants; each caller returns the generator to its own consumer and builds the query dict per call, so the query mutation at this point is not read afterwards.",
"Same query state as the original (starting and limit are updated before the return); only the extra api_method call is skipped. Output is unchanged because the original returns at the first item of the extra page. Edge: a limit of 0 with empty pages can differ in how many requests are made.")

# 2. truncate_message: bisection instead of byte-at-a-time loop
add("C7S1-truncate-bisect", "C7.S1", "src/python/dxpy/dxlog.py", "DXLogHandler.truncate_message", [(
'''        msg_bytes = msg_bytes[:8000]
        while len(json.dumps(_bytes2utf8(msg_bytes))) > 8000:
            msg_bytes = msg_bytes[:-1]
''',
'''        low, high = 0, 8000
        while low < high:
            middle = (low + high + 1) // 2
            if len(json.dumps(_bytes2utf8(msg_bytes[:middle]))) <= 8000:
                low = middle
            else:
                high = middle - 1
        msg_bytes = msg_bytes[:low]
''')],
"grep of src/python: truncate_message is called only from DXLogHandler.emit (dxlog.py line 94) through self; nothing else reads the handler's state here.",
"The JSON length of the decoded prefix is non-decreasing in the prefix length, so bisection returns the same largest prefix the original loop reaches by stepping down one byte at a time.")

# 3. spelling_corrector.correct: edits computed once
add("C1S4-correct-edits-once", "C1.S4", "src/python/dxpy/utils/spelling_corrector.py", "correct", [(
'''    candidates = _known([word], NWORDS) or _known(_edits1(word), NWORDS) or _known_edits2(word, NWORDS) or [word]
''',
'''    candidates = _known([word], NWORDS)
    if not candidates:
        edits = _edits1(word)
        candidates = _known(edits, NWORDS) or set(e2 for e1 in edits for e2 in _edits1(e1) if e2 in NWORDS) or [word]
''')],
"grep of src/python: correct is called once, from dx.py line 4559 (choice suggestions). _known_edits2 is left in place and unused by correct.",
"The original computes _edits1(word) in the one-edit clause and again inside _known_edits2 when that clause is empty. Computing it once and reusing the same set gives the same candidates, in the same iteration order. An earlier version of step 2 said the module had no callers in src/python; that was wrong, and dx.py line 4559 calls it.")

# 4. validate_JSON: drop the unused schema read
add("C1S1-validate-json-dead-read", "C1.S1", "src/python/dxpy/dx_extract_utils/filter_to_payload.py", "validate_JSON", [(
'''    schema_file = "retrieve_{}_schema.json".format(type)

''', ''),
('''    # Open the schema asset.
    with open(os.path.join(extract_utils_basepath, schema_file), "r") as infile:
        json_schema = json.load(infile)

''', '')],
"grep of src/python: validate_JSON is called from dataset_utilities.py lines 631 and test_extract_assay.py lines 339 and 353.",
"Expected to differ: the removed read raises FileNotFoundError for a type with no schema file, and the repair no longer does. This is the behaviour the schema read was providing, so a not_equivalent result here is a finding about the unit, not a bad edit.")

# 5. harmonize_germline_sql: column list loaded once per process
add("C8S2-harmonize-cached-columns", "C8.S2", "src/python/dxpy/dx_extract_utils/germline_utils.py", "harmonize_germline_sql", [(
'''    with open(os.path.join(extract_utils_basepath, "return_columns_genotype.json")) as infile:
        genotype_return_columns = json.load(infile)
''',
'''    if not hasattr(harmonize_germline_sql, "genotype_return_columns"):
        with open(os.path.join(extract_utils_basepath, "return_columns_genotype.json")) as infile:
            harmonize_germline_sql.genotype_return_columns = json.load(infile)
    genotype_return_columns = harmonize_germline_sql.genotype_return_columns
''')],
"grep of src/python: harmonize_germline_sql is called from dataset_utilities.py line 1072 only. _harmonize_sql_select_named_expression reads return_columns and does not mutate it (germline_utils.py lines 91-118), so sharing the loaded list is safe.",
"The file content is fixed, so caching it on the function object gives the same value on every call. The cache lives on the function, not in a new module-level name.")

# 6. is_list_of_strings (dx_extract input_validation): version test hoisted out of the loop
HOIST_OLD = '''    for item in object:
        # Note that in python 2.7 these strings are read in as unicode
        if python_version == 2:
            if not (isinstance(item, str) or isinstance(item, unicode)):
                return False
        else:
            if not isinstance(item, str):
                return False
    return True
'''
HOIST_NEW = '''    if python_version == 2:
        for item in object:
            # Note that in python 2.7 these strings are read in as unicode
            if not (isinstance(item, str) or isinstance(item, unicode)):
                return False
    else:
        for item in object:
            if not isinstance(item, str):
                return False
    return True
'''
add("C3S2-list-of-strings-hoist", "C3.S2", "src/python/dxpy/dx_extract_utils/input_validation.py", "is_list_of_strings",
    [(HOIST_OLD, HOIST_NEW)],
    "grep of src/python: called from input_validation.py lines 52-219 and input_validation_somatic.py; the function returns a bool and changes nothing else.",
    "python_version is a module constant set from sys.version_info, so the branch is the same for every item and can be taken once.")
add("C3S2-list-of-strings-hoist-somatic", "C3.S2", "src/python/dxpy/dx_extract_utils/input_validation_somatic.py", "is_list_of_strings",
    [(HOIST_OLD.replace('    for item in object:\n        # Note that in python 2.7 these strings are read in as unicode\n', '    for item in object:\n        # Note that in python 2.7 these strings are read in as unicode\n'), HOIST_NEW)],
    "grep of src/python: called from input_validation_somatic.py lines 39-132; the function returns a bool and changes nothing else.",
    "Same hoist as the non-somatic copy. The module-level python_version is defined in input_validation_somatic.py.")

# 7. validate_infer_flags: message built only on the error paths
src_lines = open(ROOT + 'src/python/dxpy/dx_extract_utils/input_validation.py').read().splitlines()
msg_line = next(l for l in src_lines if l.lstrip().startswith('ingestion_parameters_str = f"'))
ins = "            " + msg_line.strip() + "\n"
add("C1S6-infer-flags-lazy-message", "C1.S6", "src/python/dxpy/dx_extract_utils/input_validation.py", "validate_infer_flags", [
    (msg_line + "\n", ""),
    ("            err_exit(\n                f\"The --infer-ref flag", ins + "            err_exit(\n                f\"The --infer-ref flag"),
    ("            err_exit(\n                f\"The --infer-nocall flag", ins + "            err_exit(\n                f\"The --infer-nocall flag"),
],
"grep of src/python: validate_infer_flags is called from input_validation.py line 322 only.",
"The f-string is built only on the two error branches, where it is printed. On the common path with no infer flag, the three str().lower() conversions are no longer run.")

# 8. create_coding_name_dframe (method): display position dict built once
add("C3S4-coding-display-index-dict", "C3.S4", "src/python/dxpy/cli/dataset_utilities.py", "DXDatasetDictionary.create_coding_name_dframe", [
    ('''            display = coding.get("display") or []
''', '''            display = coding.get("display") or []
            display_order_of = {}
            for position, code in enumerate(display):
                display_order_of.setdefault(code, position + 1)
'''),
    ('''                        int(display.index(c) + 1) if c in display else None
''', '''                        int(display_order_of[c]) if c in display_order_of else None
'''),
],
"grep of src/python: create_coding_name_dframe is called from dataset_utilities.py line 2225 only.",
"display.index(c) returns the first position, and setdefault keeps the first position too, so each code maps to the same 1-based order. Assumes display items are hashable, which codes are.")

with open(OUT, 'w') as fh:
    for s in subs:
        fh.write(json.dumps(s) + '\n')
print('wrote', len(subs), 'submissions to', OUT)
