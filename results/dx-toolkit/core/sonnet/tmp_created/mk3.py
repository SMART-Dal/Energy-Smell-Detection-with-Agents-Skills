import ast, json, textwrap
P="src/python/dxpy/"
def src(path, q):
    text=open(P+path).read(); lines=text.split("\n"); t=ast.parse(text); found=None
    def walk(n,pre):
        nonlocal found
        for c in ast.iter_child_nodes(n):
            if isinstance(c,(ast.FunctionDef,ast.ClassDef)):
                if pre+c.name==q: found=c
                walk(c,pre+c.name+".")
    walk(t,"")
    start=min([found.lineno]+[d.lineno for d in found.decorator_list])
    return textwrap.dedent("\n".join(lines[start-1:found.end_lineno]))
def sub(path,q,*pairs):
    s=src(path,q)
    import re
    for old,new in pairs:
        if "." in q:
            old=re.sub(r"(?m)^    ","",old); new=re.sub(r"(?m)^    ","",new)
        assert s.count(old)==1,(q,old,s.count(old))
        s=s.replace(old,new)
    return s
S=[]
def add(id,unit_path,unit_q,changed,evidence=None,notes=""):
    ch={P+p+"::"+q:body for (p,q),body in changed.items()}
    S.append({"id":id,"unit":P+unit_path+"::"+unit_q,"changed":ch,"sole_caller_evidence":evidence,"notes":notes})

# 1 spelling corrector
add("spell-edits2","utils/spelling_corrector.py","_known_edits2",{("utils/spelling_corrector.py","_known_edits2"):'''def _known_edits2(word, NWORDS):
    e1s = _edits1(word)
    by_len = {}
    for e1 in e1s:
        by_len.setdefault(len(e1), []).append(e1)

    def reaches(a, w):
        # True when w is in _edits1(a)
        m, n = len(a), len(w)
        if n == m - 1:
            k = 0
            while k < n and a[k] == w[k]:
                k += 1
            return a[k + 1:] == w[k:]
        if n == m + 1:
            k = 0
            while k < m and a[k] == w[k]:
                k += 1
            return w[k] in _alphabet and a[k:] == w[k + 1:]
        if n != m:
            return False
        diff = [i for i in range(m) if a[i] != w[i]]
        if not diff:
            return any(c in _alphabet for c in a) or any(a[i] == a[i + 1] for i in range(m - 1))
        if len(diff) == 1:
            return w[diff[0]] in _alphabet
        if len(diff) == 2 and diff[1] == diff[0] + 1:
            i = diff[0]
            return a[i] == w[i + 1] and a[i + 1] == w[i]
        return False

    found = set()
    for w in NWORDS:
        n = len(w)
        for ln in (n - 1, n, n + 1):
            for e1 in by_len.get(ln, ()):
                if reaches(e1, w):
                    found.add(w)
                    break
            if w in found:
                break
    return found
'''},None,"The distance-2 enumeration is replaced by a direct 'is w one edit from e1' test against the ~500 distance-1 strings; `correct` reaches it through this function only (same_repair_as for correct.a).")

R="utils/resolver.py"
add("resolver-last-pos",R,"get_last_pos_of_char",{(R,"get_last_pos_of_char"):sub(R,"get_last_pos_of_char",("pos = string[:pos].rfind(char)","pos = string.rfind(char, 0, pos)"))})
add("resolver-first-pos",R,"get_first_pos_of_char",{(R,"get_first_pos_of_char"):'''def get_first_pos_of_char(char, string):
    \'\'\'
    :param char: The character to find
    :type char: string
    :param string: The string in which to search for *char*
    :type string: string
    :returns: Index in *string* where *char* last appears (unescaped by a preceding "\\\\"), -1 if not found
    :rtype: int

    Finds the first occurrence of *char* in *string* in which *char* is
    not present as an escaped character.

    \'\'\'
    pos = string.find(char)
    while pos != -1:
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            return pos
        pos = string.find(char, pos + 1)
    return -1
'''})
add("resolver-split",R,"split_unescaped",{(R,"split_unescaped"):sub(R,"split_unescaped",("pos = get_last_pos_of_char(char, string[:lastpos])","pos = _last_unescaped(string, char, lastpos)"))} if False else {(R,"split_unescaped"):'''def split_unescaped(char, string, include_empty_strings=False):
    \'\'\'
    :param char: The character on which to split the string
    :type char: string
    :param string: The string to split
    :type string: string
    :returns: List of substrings of *string*
    :rtype: list of strings

    Splits *string* whenever *char* appears without an odd number of
    backslashes ('\\\\') preceding it, discarding any empty string
    elements.

    \'\'\'
    words = []
    pos = len(string)
    lastpos = pos
    while pos >= 0:
        pos = lastpos
        while True:
            pos = string.rfind(char, 0, pos)
            if pos == -1:
                break
            num_backslashes = 0
            test_index = pos - 1
            while test_index >= 0 and string[test_index] == '\\\\':
                num_backslashes += 1
                test_index -= 1
            if num_backslashes % 2 == 0:
                break
        if pos >= 0:
            if pos + 1 != lastpos or include_empty_strings:
                words.append(string[pos + 1: lastpos])
            lastpos = pos
    if lastpos != 0 or include_empty_strings:
        words.append(string[:lastpos])
    words.reverse()
    return words
'''},None,"Scan is inlined with an end bound on rfind so no `string[:lastpos]` copy is made per piece; semantics of get_last_pos_of_char are copied exactly (including its `pos > 0` stop condition handled below).")
add("resolver-dxlink",R,"_maybe_convert_stringified_dxlink",{(R,"_maybe_convert_stringified_dxlink"):sub(R,"_maybe_convert_stringified_dxlink",("    try:\n        possible_hash","    if isinstance(path, str) and not path.lstrip().startswith('{'):\n        return path\n    try:\n        possible_hash"))})
add("resolver-colon",R,"resolve_path",{(R,"resolve_path"):sub(R,"resolve_path",("elif get_last_pos_of_char(':', path) >= 0:","elif last_colon >= 0:"))})

PP="utils/pretty_print.py"
add("pp-escape",PP,"escape_unicode_string",{(PP,"escape_unicode_string"):'''def escape_unicode_string(u):
    """
    Escapes the nonprintable chars 0-31 and 127, and backslash;
    preferably with a friendly equivalent such as '\\n' if available, but
    otherwise with a Python-style backslashed hex escape.
    """
    if re.search("[\\\\000-\\\\037\\\\134\\\\177]", u) is None:
        return u
    def replacer(matchobj):
        if ord(matchobj.group(1)) == 127:
            return "\\\\x7f"
        if ord(matchobj.group(1)) == 92: # backslash
            return "\\\\\\\\"
        return REPLACEMENT_TABLE[ord(matchobj.group(1))]
    return re.sub("([\\\\000-\\\\037\\\\134\\\\177])", replacer, u)
'''})
add("pp-table-len",PP,"format_table",{(PP,"format_table"):sub(PP,"format_table",("col_widths = [0] * len(list(table)[0])","col_widths = [0] * len(next(iter(table)))"))})
add("pp-flatten",PP,"flatten_json_array",{(PP,"flatten_json_array"):'''def flatten_json_array(json_string, array_name):
    """
    Flattens all arrays with the same name in the JSON string

    :param json_string: JSON string
    :type json_string: str
    :param array_name: Array name to flatten
    :type array_name: str
    """

    result = re.sub('"{}": \\\\[\\r?\\n\\\\s*'.format(array_name), '"{}": ['.format(array_name), json_string, flags=re.MULTILINE)
    joiner = re.compile('(?<=,)\\r?\\n\\\\s*', flags=re.MULTILINE)
    flatten_regexp = re.compile('"{}": \\\\[(?:[^\\r\\n]|\\r(?!\\n))*(?:(?<=,)\\r?\\n\\\\s*(?:[^\\r\\n]|\\r(?!\\n))*)*'.format(array_name), flags=re.MULTILINE)
    result = flatten_regexp.sub(lambda m: joiner.sub(' ', m.group(0)), result)
    result = re.sub('"{}": \\\\[(.*)\\r?\\n\\\\s*\\\\]'.format(array_name), '"{}": [\\\\1]'.format(array_name), result, flags=re.MULTILINE)
    return result
'''},None,"One pass joins every comma-terminated line of each array instead of one line per pass; fuzzed against the original before submission.")

DL="dxlog.py"
add("dxlog-encode",DL,"DXLogHandler.truncate_message",{(DL,"DXLogHandler.truncate_message"):sub(DL,"DXLogHandler.truncate_message",("        msg_bytes = message.encode('utf-8')\n\n        if len(json.dumps(message)) <= 8015:\n            return message\n\n","        if len(json.dumps(message)) <= 8015:\n            return message\n\n        msg_bytes = message.encode('utf-8')\n"))})
add("dxlog-bsearch",DL,"DXLogHandler.truncate_message",{(DL,"DXLogHandler.truncate_message"):sub(DL,"DXLogHandler.truncate_message",("        msg_bytes = msg_bytes[:8000]\n        while len(json.dumps(_bytes2utf8(msg_bytes))) > 8000:\n            msg_bytes = msg_bytes[:-1]\n","        msg_bytes = msg_bytes[:8000]\n        lo, hi = 0, len(msg_bytes)\n        while lo < hi:\n            mid = (lo + hi + 1) // 2\n            if len(json.dumps(_bytes2utf8(msg_bytes[:mid]))) > 8000:\n                hi = mid - 1\n            else:\n                lo = mid\n        msg_bytes = msg_bytes[:lo]\n"))},None,"len(json.dumps(decoded prefix)) is non-decreasing in the prefix length, so the largest prefix within 8000 found by bisection equals the one the byte-at-a-time loop stops at.")

CF="dx_extract_utils/cohort_filter_payload.py"
add("cohort-pheno-reduce",CF,"generate_pheno_filter",{(CF,"generate_pheno_filter"):sub(CF,"generate_pheno_filter",
  ('values = sorted(set(values).intersection(set(reduce(lambda_for_list_conv, primary_filter["values"], []))))','values = sorted(set(values).intersection(set([lambda_for_list_conv([], b)[0] for b in primary_filter["values"]])))'),
  ('values = sorted(set(values) - set(reduce(lambda_for_list_conv, primary_filter["values"], [])))','values = sorted(set(values) - set([lambda_for_list_conv([], b)[0] for b in primary_filter["values"]]))'))},None,"lambda_for_list_conv is `lambda a, b: a+[conv(b)]` at its only definition sites (validate_cohort_ids); calling it with an empty list returns [conv(b)]. `reduce` is still imported for other users in the module.")

DD="cli/dataset_utilities.py"
add("dd-coding-index",DD,"DXDatasetDictionary.create_coding_name_dframe",{(DD,"DXDatasetDictionary.create_coding_name_dframe"):sub(DD,"DXDatasetDictionary.create_coding_name_dframe",
 ('''            display = coding.get("display") or []
''','''            display = coding.get("display") or []
            display_pos = {}
            for i, c in enumerate(display):
                display_pos.setdefault(c, i)
'''),
 ('''                        int(display.index(c) + 1) if c in display else None
''','''                        int(display_pos[c] + 1) if c in display_pos else None
'''))})
add("dd-load-assign",DD,"DXDatasetDictionary.load_data_dictionary",{(DD,"DXDatasetDictionary.load_data_dictionary"):sub(DD,"DXDatasetDictionary.load_data_dictionary",('''
                source_eblock = source_eblock.assign(
                    relationship=rel, referenced_entity_field=ref
                )
''',''))})
FP="dx_extract_utils/filter_to_payload.py"
add("fp-validate",FP,"validate_JSON",{(FP,"validate_JSON"):sub(FP,"validate_JSON",('''    schema_file = "retrieve_{}_schema.json".format(type)

    # Open the schema asset.
    with open(os.path.join(extract_utils_basepath, schema_file), "r") as infile:
        json_schema = json.load(infile)

''',''))})
GU="dx_extract_utils/germline_utils.py"
add("gu-harmonize-results",GU,"harmonize_germline_results",{(GU,"harmonize_germline_results"):'''def harmonize_germline_results(results, fields_list):
    """
    Harmonizes raw query results to include all columns in fields_list. Columns not in fields_list have value None.
    """
    return [{field: result.get(field) for field in fields_list} for result in results]
'''},None,"`result` rows are dicts (JSON query results); `field in result` then `result[field]` equals `.get(field)` except when a key is present with value None, which gives None either way.")
add("gu-infer-hoist",GU,"infer_genotype_type",{(GU,"infer_genotype_type"):sub(GU,"infer_genotype_type",('''    for locus in loci_dict:
        for sample in samples:
            if sample not in loci_dict[locus]["samples"]:
                inferred_entries.append(
                    {
                        "sample_id": sample,
                        **loci_dict[locus]["entry"],
''','''    for locus in loci_dict:
        locus_info = loci_dict[locus]
        locus_samples = locus_info["samples"]
        locus_entry = locus_info["entry"]
        for sample in samples:
            if sample not in locus_samples:
                inferred_entries.append(
                    {
                        "sample_id": sample,
                        **locus_entry,
'''))})
OH="cli/output_handling.py"
add("oh-sets",OH,"write_expression_output",{(OH,"write_expression_output"):sub(OH,"write_expression_output",('''        if not all(
            set(i.keys()) == set(COLUMN_NAMES) for i in output_listdict_or_string
        ):''','''        expected_columns = set(COLUMN_NAMES)
        if not all(
            i.keys() == expected_columns for i in output_listdict_or_string
        ):'''))})
NT="nextflow/nextflow_templates.py"
add("nt-concat",NT,"get_nextflow_src",{(NT,"get_nextflow_src"):sub(NT,"get_nextflow_src",
 ('''    exclude_input_download = ""
    applet_runtime_params = ""
''','''    exclude_input_parts = []
    applet_runtime_parts = []
'''),
 ('''            exclude_input_download += "--except {} ".format(i['name'])''','''            exclude_input_parts.append("--except {} ".format(i['name']))'''),
 ('''        applet_runtime_params = applet_runtime_params + \'\'\'
        if [ -n "${}" ]; then
            applet_runtime_inputs+=(--{} "{}")
        fi
        \'\'\'.format(i['name'], i['name'], value)
''','''        applet_runtime_parts.append(\'\'\'
        if [ -n "${}" ]; then
            applet_runtime_inputs+=(--{} "{}")
        fi
        \'\'\'.format(i['name'], i['name'], value))
'''),
 ('''    profile_arg =''','''    exclude_input_download = "".join(exclude_input_parts)
    applet_runtime_params = "".join(applet_runtime_parts)
    profile_arg ='''))})
NB="nextflow/nextflow_builder.py"
add("nb-required-set",NB,"prepare_custom_inputs",{(NB,"prepare_custom_inputs"):sub(NB,"prepare_custom_inputs",('required_inputs = d_schema.get("required", [])','required_inputs = set(d_schema.get("required", []))'))},None,"required_inputs is read only by the two membership tests in this loop; JSON `required` entries are strings so hashable.")
add("nb-insert",NB,"prepare_custom_inputs",{(NB,"prepare_custom_inputs"):sub(NB,"prepare_custom_inputs",
 ("    inputs = []\n    if not os.path.exists(schema_file):\n        return inputs\n","    inputs = []\n    required_list = []\n    if not os.path.exists(schema_file):\n        return inputs\n"),
 ("                inputs.insert(0, dx_input)\n","                required_list.append(dx_input)\n"),
 ("                inputs.append(dx_input)\n\n    return inputs","                inputs.append(dx_input)\n\n    required_list.reverse()\n    return required_list + inputs"))})
DE="utils/describe.py"
add("describe-locale",DE,"format_currency",{(DE,"format_currency"):sub(DE,"format_currency",("            locale.setlocale(locale.LC_ALL, currency_locale)\n","            if locale.setlocale(locale.LC_ALL) != currency_locale:\n                locale.setlocale(locale.LC_ALL, currency_locale)\n"))})
SR="system_requirements.py"
add("sr-cluster-copy",SR,"SystemRequirementsDict.override_cluster_spec",{(SR,"SystemRequirementsDict.override_cluster_spec"):sub(SR,"SystemRequirementsDict.override_cluster_spec",
 ('''        merged_cluster_spec = copy.deepcopy(self.entrypoints)

        # Remove entrypoints without "clusterSpec"
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if v.get("clusterSpec") is not None])

        # Remove entrypoints not provided in requested instance counts
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if \\
            k in srd.entrypoints or "*" in srd.entrypoints])
''','''        # Remove entrypoints without "clusterSpec"
        merged_cluster_spec = dict([(k, v) for k, v in self.entrypoints.items() if v.get("clusterSpec") is not None])

        # Remove entrypoints not provided in requested instance counts
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if \\
            k in srd.entrypoints or "*" in srd.entrypoints])
        merged_cluster_spec = copy.deepcopy(merged_cluster_spec)
'''))})
SE="bindings/search.py"
add("search-limit",SE,"_find",{(SE,"_find"):sub(SE,"_find",('''            num_results += 1
            yield format_result(i)
''','''            num_results += 1
            yield format_result(i)
            if num_results == limit:
                return
'''))},None,"`_find` is private to search.py; callers are the find_* wrappers via `_find`; after the limit-th yield the original loop either returned at the next item or fetched a page it then dropped, so returning early yields the same items.")
with open("submissions.jsonl","w") as f:
    for s in S: f.write(json.dumps(s)+"\n")
print(len(S))
