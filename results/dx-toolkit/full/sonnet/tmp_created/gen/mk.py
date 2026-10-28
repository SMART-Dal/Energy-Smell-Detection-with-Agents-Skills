import ast, json, textwrap, sys
REPO="/home/javad/energy-run/dx-toolkit/"
P="src/python/dxpy/"
subs=[]
def ded(x):
    return "\n".join(l[4:] if l.startswith("    ") else l for l in x.split("\n"))
def fsrc(path, qn, raw=False):
    src=open(REPO+path).read()
    lines=src.split("\n")
    t=ast.parse(src)
    parts=qn.split(".")
    node=t
    for p in parts:
        for c in ast.iter_child_nodes(node):
            if isinstance(c,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)) and c.name==p:
                node=c;break
        else: raise KeyError(qn)
    start=min([node.lineno]+[d.lineno for d in node.decorator_list])
    text="\n".join(lines[start-1:node.end_lineno])
    if raw: return text
    return textwrap.dedent(text)
def mk(id_, rc, unit, edits, notes, evidence=None, full=None):
    path,qn=unit.split("::")
    path=P+path
    text=fsrc(path,qn)
    is_method = fsrc(path,qn,raw=True).startswith(" ")
    if is_method and edits:
        edits=[(ded(a),ded(b)) for a,b in edits]
    if full is not None:
        new=full
    else:
        new=text
        for old,rep in edits:
            assert new.count(old)==1,(id_,old[:60],new.count(old))
            new=new.replace(old,rep)
    assert new!=text
    subs.append({"id":id_,"root_cause":rc,"unit":path+"::"+qn,"changed":{path+"::"+qn:new},"sole_caller_evidence":evidence,"notes":notes})

# 1 get_first_pos_of_char
mk("C3S5-first-pos","C3.S5","utils/resolver.py::get_first_pos_of_char",[(
"""    first_pos = -1
    pos = len(string)
    while pos > 0:
        pos = string[:pos].rfind(char)
        if pos == -1:
            return first_pos
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            first_pos = pos
    return first_pos""",
"""    pos = string.find(char)
    while pos != -1:
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            return pos
        pos = string.find(char, pos + 1)
    return -1""")],"C3.S5 (close to C6.S2, which is about the slice copy). Scans forward and stops at the first unescaped hit; callers all pass a single character.")
# 2 get_last_pos_of_char
mk("C6S2-last-pos","C6.S2","utils/resolver.py::get_last_pos_of_char",[("pos = string[:pos].rfind(char)","pos = string.rfind(char, 0, pos)")],"`string.rfind(char, 0, pos)` searches the same prefix without allocating the slice.")
# 3 split_unescaped
mk("C7S1-split-unescaped","C7.S1","utils/resolver.py::split_unescaped",[(
"""    words = []
    pos = len(string)
    lastpos = pos
    while pos >= 0:
        pos = get_last_pos_of_char(char, string[:lastpos])
        if pos >= 0:
            if pos + 1 != lastpos or include_empty_strings:
                words.append(string[pos + 1: lastpos])
            lastpos = pos
    if lastpos != 0 or include_empty_strings:
        words.append(string[:lastpos])
    words.reverse()
    return words""",
"""    words = []
    start = 0
    pos = string.find(char)
    while pos != -1:
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            if pos != start or include_empty_strings:
                words.append(string[start:pos])
            start = pos + 1
        pos = string.find(char, pos + 1)
    if start != len(string) or include_empty_strings:
        words.append(string[start:])
    return words""")],"One forward pass instead of one right-to-left rescan with slicing per token; single-character separators only (every caller passes one).")
# 4 is_glob_pattern
mk("C4S7-is-glob","C4.S7","utils/resolver.py::is_glob_pattern",[("    return (get_last_pos_of_char('*', string) >= 0)","    if '*' not in string and '?' not in string:\n        return False\n    return (get_last_pos_of_char('*', string) >= 0)")],"Cheap membership test first; strings with neither character skip two escape-aware scans.")
# 5 escape_folder_str
mk("C10S1-escape-folder","C10.S1","utils/resolver.py::escape_folder_str",None and [],"Single `str.translate` with a table kept as a function attribute replaces replace + re.sub with a callback.",full='''def escape_folder_str(string):
    try:
        table = escape_folder_str._table
    except AttributeError:
        table = {ord(c): '\\\\' + c for c in "#?*: ;&`\\"'!$(){[<>|~"}
        table[92] = '\\\\\\\\'
        escape_folder_str._table = table
    return str.translate(string, table)''')
# 6 flatten_json_array
mk("C1S4-flatten-subn","C1.S4","utils/pretty_print.py::flatten_json_array",[(
"""    while flatten_regexp.search(result):
        result = flatten_regexp.sub('"{}": [\\\\1 '.format(array_name), result)""",
"""    while True:
        result, count = flatten_regexp.subn('"{}": [\\\\1 '.format(array_name), result)
        if count == 0:
            break""")],"`subn` reports whether it replaced anything, so the extra `search` over the whole text per pass goes.")
# 7 escape_unicode_string
mk("C10S1-escape-unicode","C10.S1","utils/pretty_print.py::escape_unicode_string",None,"`str.translate` with a table built once from REPLACEMENT_TABLE replaces re.sub with a Python callback per match.",full='''def escape_unicode_string(u):
    """
    Escapes the nonprintable chars 0-31 and 127, and backslash;
    preferably with a friendly equivalent such as '\\n' if available, but
    otherwise with a Python-style backslashed hex escape.
    """
    try:
        table = escape_unicode_string._table
    except AttributeError:
        table = {i: REPLACEMENT_TABLE[i] for i in range(32)}
        table[127] = "\\\\x7f"
        table[92] = "\\\\\\\\"
        escape_unicode_string._table = table
    return str.translate(u, table)''')
# 8 format_table a
mk("C6S3-table-first-row","C6.S3","utils/pretty_print.py::format_table",[("col_widths = [0] * len(list(table)[0])","col_widths = [0] * len(table[0])")],"Reads the first row directly instead of copying the table to a list.")
mk("C3S2-table-border","C3.S2","utils/pretty_print.py::format_table",[(
"""    for row in my_table:
        padded_row = [row[i] + ' '*(col_widths[i]-len(row[i])) for i in range(len(row))]
        formatted_table.append(border('│') + border('│').join(padded_row) + border('│'))""",
"""    row_border = border('│')
    for row in my_table:
        padded_row = [row[i] + ' '*(col_widths[i]-len(row[i])) for i in range(len(row))]
        formatted_table.append(row_border + row_border.join(padded_row) + row_border)""")],"The vertical border string is constant, so it is built once before the row loop instead of three times per row.")
# 9 _edits1
mk("C6S2-edits1-set","C6.S2","utils/spelling_corrector.py::_edits1",[(
"""   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in _alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in _alphabet]
   return set(deletes + transposes + replaces + inserts)""",
"""   edits = set(a + b[1:] for a, b in splits if b)
   edits.update(a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1)
   edits.update(a + c + b[1:] for a, b in splits for c in _alphabet if b)
   edits.update(a + c + b     for a, b in splits for c in _alphabet)
   return edits""")],"One set filled from four generators replaces four lists, their concatenation and a final set copy.",evidence=None)
# 10 truncate_message
mk("C4S7-truncate-guard","C4.S7","dxlog.py::DXLogHandler.truncate_message",[(
"""        msg_bytes = message.encode('utf-8')

        if len(json.dumps(message)) <= 8015:""",
"""        if isinstance(message, str) and len(message) <= 667:
            return message

        msg_bytes = message.encode('utf-8')

        if len(json.dumps(message)) <= 8015:""")],"A str of at most 667 characters encodes to at most 667*12+2 = 8006 JSON bytes (a non-BMP char is 12 escaped bytes), so it always passes the 8015 test; the encode and dumps are skipped for it. Lone surrogates no longer raise UnicodeEncodeError from the early encode.")
# 11 coding display order
mk("C3S4-coding-display-index","C3.S4","cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe",[(
"""            display = coding.get("display") or []
            dcols.update(""",
"""            display = coding.get("display") or []
            display_pos = {}
            for i, c in enumerate(display):
                display_pos.setdefault(c, i + 1)
            dcols.update("""),(
"""                        int(display.index(c) + 1) if c in display else None
                        for c in codes""",
"""                        display_pos.get(c)
                        for c in codes""")],"`display.index(c)` plus `c in display` are two linear scans per code; a first-occurrence position dict built once answers both.")
# 12 final_payload
mk("C8S1-final-payload-columns","C8.S1","dx_extract_utils/filter_to_payload.py::final_payload",[(
"""    if filter_type == "allele":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_allele.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "annotation":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_annotation.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "genotype":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_genotype.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "genotype_only":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_genotype_only.json"), "r"
        ) as infile:
            fields = json.load(infile)
""",
"""    if filter_type in ("allele", "annotation", "genotype", "genotype_only"):
        columns_text = globals().setdefault("_return_columns_text", {})
        if filter_type not in columns_text:
            with open(
                os.path.join(extract_utils_basepath, "return_columns_%s.json" % filter_type), "r"
            ) as infile:
                columns_text[filter_type] = infile.read()
        fields = json.loads(columns_text[filter_type])
""")],"The file text is cached per filter type; each call still parses a fresh object, because callers append to payload['fields'] (dataset_utilities.extract_assay_germline).")
# 13 harmonize_germline_sql
mk("C8S1-harmonize-columns","C8.S1","dx_extract_utils/germline_utils.py::harmonize_germline_sql",[(
"""    with open(os.path.join(extract_utils_basepath, "return_columns_genotype.json")) as infile:
        genotype_return_columns = json.load(infile)""",
"""    genotype_return_columns = globals().get("_genotype_return_columns")
    if genotype_return_columns is None:
        with open(os.path.join(extract_utils_basepath, "return_columns_genotype.json")) as infile:
            genotype_return_columns = globals().setdefault("_genotype_return_columns", json.load(infile))""")],"The parsed list is kept after the first call; its only reader is `_harmonize_sql_select_named_expression`, which does not modify it.",evidence="`genotype_return_columns` is a local read once by `_harmonize_sql_select_named_expression(sql, return_columns, ...)`, which only iterates it (germline_utils.py lines 91-118); grep shows no other reader of return_columns_genotype.json in this function's path.")
# 15 normalize_timedelta
mk("C4S6-timedelta-suffix","C4.S6","utils/__init__.py::normalize_timedelta",[(
"""    try:
        return int(timedelta) * 1000
    except ValueError as e:
        t, suffix = timedelta[:-1], timedelta[-1:]
        suffix_multipliers = {'s': 1000, 'm': 1000*60, 'h': 1000*60*60, 'd': 1000*60*60*24, 'w': 1000*60*60*24*7,
                              'M': 1000*60*60*24*30, 'y': 1000*60*60*24*365}
        if suffix not in suffix_multipliers:""",
"""    suffix_multipliers = {'s': 1000, 'm': 1000*60, 'h': 1000*60*60, 'd': 1000*60*60*24, 'w': 1000*60*60*24*7,
                          'M': 1000*60*60*24*30, 'y': 1000*60*60*24*365}
    if isinstance(timedelta, str) and timedelta[-1:] in suffix_multipliers:
        return int(timedelta[:-1]) * suffix_multipliers[timedelta[-1:]]
    try:
        return int(timedelta) * 1000
    except ValueError as e:
        t, suffix = timedelta[:-1], timedelta[-1:]
        if suffix not in suffix_multipliers:""")],"A string ending in a suffix letter can never be an int, so the failing int() call (and its exception) is skipped for the common '5d' form.")
# 16 get_nextflow_src
mk("C10S4-nextflow-src-join","C10.S4","nextflow/nextflow_templates.py::get_nextflow_src",[(
"""    exclude_input_download = ""
    applet_runtime_params = ""
    for i in custom_inputs:""",
"""    exclude_parts = []
    runtime_parts = []
    for i in custom_inputs:"""),(
"""            exclude_input_download += "--except {} ".format(i['name'])""",
"""            exclude_parts.append("--except {} ".format(i['name']))"""),(
"""        applet_runtime_params = applet_runtime_params + '''
        if [ -n "${}" ]; then
            applet_runtime_inputs+=(--{} "{}")
        fi
        '''.format(i['name'], i['name'], value)
""",
"""        runtime_parts.append('''
        if [ -n "${}" ]; then
            applet_runtime_inputs+=(--{} "{}")
        fi
        '''.format(i['name'], i['name'], value))

    exclude_input_download = "".join(exclude_parts)
    applet_runtime_params = "".join(runtime_parts)
""")],"Parts are collected and joined once. The original concatenation targets locals, which CPython can often resize in place, so the gain may be small.")
# 17 _load_versions_manifest
mk("C8S1-versions-manifest","C8.S1","nextflow/nextflow_utils.py::_load_versions_manifest",[(
"""    manifest_path = path.join(path.dirname(dxpy.__file__), 'nextflow', 'versions.json')
    try:""",
"""    manifest_path = path.join(path.dirname(dxpy.__file__), 'nextflow', 'versions.json')
    import copy
    cache = globals().setdefault("_versions_manifest_cache", {})
    if manifest_path in cache:
        return copy.deepcopy(cache[manifest_path])
    try:"""),(
"""    return manifest""",
"""    cache[manifest_path] = copy.deepcopy(manifest)
    return manifest""")],"Validated manifest cached per path; callers get a deep copy so they can still edit what they receive.",evidence="Callers in nextflow_utils.py (resolve_version, get_versions) were read; each takes the returned dict and may index or copy it; a deep copy is returned so mutation cannot reach the cache.")
# 18 override_cluster_spec
mk("C7S4-cluster-filter-first","C7.S4","system_requirements.py::SystemRequirementsDict.override_cluster_spec",[(
"""        merged_cluster_spec = copy.deepcopy(self.entrypoints)

        # Remove entrypoints without "clusterSpec"
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if v.get("clusterSpec") is not None])

        # Remove entrypoints not provided in requested instance counts
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if \\
            k in srd.entrypoints or "*" in srd.entrypoints])
""",
"""        # Keep only entrypoints with a "clusterSpec" that were requested, copying just those
        merged_cluster_spec = dict([(k, copy.deepcopy(v)) for k, v in self.entrypoints.items()
                                    if v.get("clusterSpec") is not None and
                                    (k in srd.entrypoints or "*" in srd.entrypoints)])
""")],"Filter first, then deep-copy only the surviving entrypoints rather than all of them.")
# 19 are_list_items_within_range
mk("C1S4-range-int-once","C1.S4","bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range",[(
"""        for item in input_json[key]:
            if int(item[end_subkey]) <= int(item[start_subkey]):""",
"""        start_values = []
        end_values = []
        for item in input_json[key]:
            end_value = int(item[end_subkey])
            start_value = int(item[start_subkey])
            start_values.append(start_value)
            end_values.append(end_value)
            if end_value <= start_value:"""),(
"""            start_values = [int(item[start_subkey]) for item in input_json[key]]
            end_values = [int(item[end_subkey]) for item in input_json[key]]

""","")],"Each value is converted to int once; the two comprehension passes over the list are gone.")
# 20 ListCompleter.get_matches
mk("C1S4-listcompleter-rfind","C1.S4","utils/completer.py::ListCompleter.get_matches",[(
"""            for i in range(len(self.matches)):
                self.matches[i] = self.matches[i][self.matches[i].rfind(':') + 1:]""",
"""            for i in range(len(self.matches)):
                match = self.matches[i]
                self.matches[i] = match[match.rfind(':') + 1:]""")],"Binds the element once instead of indexing the list three times per element.")
# 21 has_local_job_refs
mk("C1S4-localrefs-bind","C1.S4","utils/local_exec_utils.py::has_local_job_refs",[(
"""    for field in io_hash:
        if is_job_ref(io_hash[field]):
            if get_job_from_jbor(io_hash[field]).startswith('localjob'):
                return True
        elif isinstance(io_hash[field], list) or isinstance(io_hash[field], dict):
            q.append(io_hash[field])""",
"""    for field in io_hash:
        value = io_hash[field]
        if is_job_ref(value):
            if get_job_from_jbor(value).startswith('localjob'):
                return True
        elif isinstance(value, list) or isinstance(value, dict):
            q.append(value)"""),(
"""            for i in range(len(thing)):
                if is_job_ref(thing[i]):
                    if get_job_from_jbor(thing[i]).startswith('localjob'):
                        return True
                elif isinstance(thing[i], list) or isinstance(thing[i], dict):
                    q.append(thing[i])
        else:
            for field in thing:
                if is_job_ref(thing[field]):
                    if get_job_from_jbor(thing[field]).startswith('localjob'):
                        return True
                elif isinstance(thing[field], list) or isinstance(thing[field], dict):
                    q.append(thing[field])""",
"""            for i in range(len(thing)):
                value = thing[i]
                if is_job_ref(value):
                    if get_job_from_jbor(value).startswith('localjob'):
                        return True
                elif isinstance(value, list) or isinstance(value, dict):
                    q.append(value)
        else:
            for field in thing:
                value = thing[field]
                if is_job_ref(value):
                    if get_job_from_jbor(value).startswith('localjob'):
                        return True
                elif isinstance(value, list) or isinstance(value, dict):
                    q.append(value)""")],"Each element is looked up once and bound, not three or four times.")
# 22 _dict_raise_on_duplicates
mk("C10S1-dupkeys-dict","C10.S1","utils/__init__.py::_dict_raise_on_duplicates",None,"`dict(pairs)` builds the mapping in C; a Python loop only runs on the error path to name the first duplicate.",full='''def _dict_raise_on_duplicates(ordered_pairs):
    """
    Reject duplicate keys.
    """
    if not isinstance(ordered_pairs, list):
        ordered_pairs = list(ordered_pairs)
    d = dict(ordered_pairs)
    if len(d) != len(ordered_pairs):
        seen = {}
        for k, v in ordered_pairs:
            if k in seen:
                raise ValueError("duplicate key: %r" % (k,))
            seen[k] = v
    return d''')
# 23 translate
mk("C10S4-glob-translate-join","C10.S4","utils/pathmatch.py::translate",None,"Parts are appended to a list and joined once instead of `res = res + ...` per pattern character; `'%s[%s]' % (res, stuff)` becomes an appended `[stuff]`.",full='''def translate(pat):
    """
    A copy of fnmatch.translate that replaces with [^\\/] instead of . to match path globs.
    """

    i, n = 0, len(pat)
    res = []
    while i < n:
        c = pat[i]
        i = i+1
        if c == '*':
            res.append('[^\\/]*')
        elif c == '?':
            res.append('[^\\/].')
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j+1
            if j < n and pat[j] == ']':
                j = j+1
            while j < n and pat[j] != ']':
                j = j+1
            if j >= n:
                res.append('\\\\[')
            else:
                stuff = pat[i:j].replace('\\\\','\\\\\\\\')
                i = j+1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\\\' + stuff
                res.append('[%s]' % (stuff,))
        else:
            res.append(re.escape(c))
    return '(?ms)' + ''.join(res) + '\\Z\'''')
# 24 write_expression_output
mk("C3S2-expr-output-set","C3.S2","cli/output_handling.py::write_expression_output",[(
"""        if not all(
            set(i.keys()) == set(COLUMN_NAMES) for i in output_listdict_or_string
        ):""",
"""        expected_columns = set(COLUMN_NAMES)
        if not all(
            set(i.keys()) == expected_columns for i in output_listdict_or_string
        ):""")],"`set(COLUMN_NAMES)` is built once, not once per row.")
# 25 _maybe_convert
mk("C4S6-dxlink-guard","C4.S6","utils/resolver.py::_maybe_convert_stringified_dxlink",[(
"""    try:
        possible_hash = json.loads(path)""",
"""    try:
        if path.lstrip(' \\t\\n\\r')[:1] != '{':
            return path
        possible_hash = json.loads(path)""")],"Only a JSON object can be a stringified dxlink, so anything not starting with '{' skips json.loads and the exception it raises.")
# 26 validate_cohort_ids
mk("C7S1-cohort-ids-comprehension","C7.S1","cli/dataset_utilities.py::validate_cohort_ids",[(
"""        lambda_for_list_conv = lambda a, b: a+[int(b)]""","""        lambda_for_list_conv = lambda a, b: a+[int(b)]
        convert = int"""),("""        lambda_for_list_conv = lambda a, b: a+[float(b)]""","""        lambda_for_list_conv = lambda a, b: a+[float(b)]
        convert = float"""),("""        lambda_for_list_conv = lambda a, b: a+[str(b)]""","""        lambda_for_list_conv = lambda a, b: a+[str(b)]
        convert = str"""),("    id_list = reduce(lambda_for_list_conv, ids, [])","    id_list = [convert(b) for b in ids]")],"The lambda is still returned for generate_pheno_filter; the id list itself is built in one pass instead of copying the accumulator at every step.",evidence="validate_cohort_ids is called once, from create_cohort (dataset_utilities.py line 1877); its return value (list, lambda) is unchanged.")
with open(REPO+"submissions.jsonl","w") as f:
    for s in subs:
        s["agent_measurement"]=None
        d=dict(s); d.pop("agent_measurement")
        f.write(json.dumps(d)+"\n")
print(len(subs))
