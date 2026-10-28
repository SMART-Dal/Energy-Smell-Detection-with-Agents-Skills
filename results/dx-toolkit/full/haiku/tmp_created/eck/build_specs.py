import json, os
R = "/home/javad/energy-run/dx-toolkit"
specs = [
 dict(id="C6S2-get-last-rfind", root_cause="C6.S2", unit="src/python/dxpy/utils/resolver.py::get_last_pos_of_char",
      edits=[["        pos = string[:pos].rfind(char)", "        pos = string.rfind(char, 0, pos)", 1]],
      evidence="Callers of get_last_pos_of_char: cli/cp.py:41, utils/completer.py:56,176,177, utils/resolver.py:178,313,345,515,517,535. Each uses only the returned index; the function reads no state and writes none. get_first_pos_of_char and split_unescaped are separate units and are not changed here.",
      notes="C6.S2. Replaces the per-iteration copy string[:pos] with rfind(char, 0, pos), which searches the same range [0, pos). Return value identical."),
 dict(id="C6S2-get-first-rfind", root_cause="C6.S2", unit="src/python/dxpy/utils/resolver.py::get_first_pos_of_char",
      edits=[["        pos = string[:pos].rfind(char)", "        pos = string.rfind(char, 0, pos)", 1]],
      evidence="Callers of get_first_pos_of_char: utils/resolver.py:1362, utils/completer.py:55, cli/download.py:146,223. Each uses only the returned index; no state is read or written.",
      notes="C6.S2. Same edit as get_last_pos_of_char, applied in this function alone: the per-occurrence copy string[:pos] becomes rfind(char, 0, pos). Return value identical."),
 dict(id="C4S6-dlink-precheck", root_cause="C4.S6", unit="src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink",
      edits=[["    try:\n        possible_hash = json.loads(path)", "    try:\n        if not path.lstrip().startswith('{'):\n            return path\n        possible_hash = json.loads(path)", 1]],
      evidence="Callers of _maybe_convert_stringified_dxlink: utils/resolver.py:198 and :487 only. The function returns path unchanged on every route that does not produce a dict.",
      notes="C4.S6. A dict can only come from text whose first non-whitespace character is '{', so the precheck returns the same value as json.loads without raising the decode error for ordinary paths. Non-str input still raises inside the try and falls back to path, as before."),
 dict(id="C3S1-pathmatch-comprehension", root_cause="C3.S1", unit="src/python/dxpy/utils/pathmatch.py::filter",
      edits=[["        for name in names:\n            if match(name):\n                result.append(name)\n", "        result = [name for name in names if match(name)]\n", 1]],
      evidence="pathmatch.filter is imported as a module by cli/download.py:34 and is not called elsewhere in src. The posix branch only; the non-posix branch is left as it was.",
      notes="C3.S1. The posix loop's explicit append becomes a list comprehension with the same match calls in the same order; result is the same list."),
 dict(id="C6S2-pheno-comprehension", root_cause="C6.S2", unit="src/python/dxpy/dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter",
      edits=[['reduce(lambda_for_list_conv, primary_filter["values"], [])', '[lambda_for_list_conv([], v)[0] for v in primary_filter["values"]]', 2]],
      evidence="generate_pheno_filter is called at dx_extract_utils/cohort_filter_payload.py:90 and by test_create_cohort.py:437 only. The lambda passed in is always a+[conv(b)], so lambda([], v)[0] is conv(v), and the list is the same as reduce's.",
      notes="C6.S2. Both reduce-with-concatenation lines (the 'in' and 'not-in' branches) become a comprehension that converts each value once. The conversion is the one passed in, so the result list, and any exception it raises, are the same."),
 dict(id="C8S3-infer-hoist", root_cause="C8.S3", unit="src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type",
      edits=[['    for locus in loci_dict:\n        for sample in samples:', '    for locus in loci_dict:\n        locus_record = loci_dict[locus]\n        for sample in samples:', 1],
             ['if sample not in loci_dict[locus]["samples"]:', 'if sample not in locus_record["samples"]:', 1],
             ['**loci_dict[locus]["entry"],', '**locus_record["entry"],', 1]],
      evidence="infer_genotype_type is called at cli/dataset_utilities.py:1113 and by test_extract_assay.py:675. Nothing inside the loop changes loci_dict, so the record is the same object on every pass.",
      notes="C8.S3. The locus record is looked up once per locus instead of once per sample. Output is the same list of entries in the same order."),
 dict(id="C1S1-validate-json-dead-read", root_cause="C1.S1", unit="src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON",
      edits=[['    schema_file = "retrieve_{}_schema.json".format(type)\n\n    # Open the schema asset.\n    with open(os.path.join(extract_utils_basepath, schema_file), "r") as infile:\n        json_schema = json.load(infile)\n\n', '', 1]],
      evidence="validate_JSON is called at cli/dataset_utilities.py:631 and by test_extract_assay.py:339,353. json_schema is read nowhere: its only use, validate(filter, json_schema), is commented out in the body.",
      notes="C1.S1. Deletes the schema open, read and parse, whose result nothing uses. Contract change to note: if the packaged schema file were missing, the original raised an OSError before validating and this version does not. The file is shipped with the package, so this does not arise for valid installs."),
 dict(id="C6S2-cluster-copy-kept", root_cause="C6.S2", unit="src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec",
      edits=[["    merged_cluster_spec = copy.deepcopy(self.entrypoints)", "    merged_cluster_spec = {k: copy.deepcopy(v) for k, v in self.entrypoints.items()\n                           if v.get(\"clusterSpec\") is not None and (k in srd.entrypoints or \"*\" in srd.entrypoints)}", 1]],
      evidence="override_cluster_spec is called at scripts/dx.py:3280 and by test_dxpy_utils.py only. The returned object is built from copies of the same kept entries, and self.entrypoints is not mutated.",
      notes="C6.S2. Copies only the entries that survive the two filters, instead of copying every entrypoint and dropping most. The two filter lines that follow are now no-ops and are left as they were, so the edit is one statement."),
 dict(id="C1S4-correct-edits-once", root_cause="C1.S4", unit="src/python/dxpy/utils/spelling_corrector.py::correct",
      edits=[["    candidates = _known([word], NWORDS) or _known(_edits1(word), NWORDS) or _known_edits2(word, NWORDS) or [word]", "    candidates = _known([word], NWORDS)\n    if not candidates:\n        edits1 = _edits1(word)\n        candidates = _known(edits1, NWORDS) or set(e2 for e1 in edits1 for e2 in _edits1(e1) if e2 in NWORDS) or [word]", 1]],
      evidence="correct is called at scripts/dx.py:4559 only. _known_edits2 is no longer called from correct and is otherwise unused; it is left in place.",
      notes="C1.S4. _edits1(word) was computed for the second stage and again inside _known_edits2 for the third stage; it is now computed once, and only when the word itself is unknown. The candidate set is the same, so the result is the same."),
]
os.makedirs("/tmp/eck/specs", exist_ok=True)
for s in specs:
    s["repo"] = R
    json.dump(s, open(f"/tmp/eck/specs/{s['id']}.json", "w"))
print(len(specs), "specs")
