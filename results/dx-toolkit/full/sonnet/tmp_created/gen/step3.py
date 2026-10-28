import json
REPO="/home/javad/energy-run/dx-toolkit/"
P="src/python/dxpy/"
subs={}
for l in open(REPO+"submissions.jsonl"):
    s=json.loads(l); subs[s['id']]=s
SUBMAP={
("utils/resolver.py::get_first_pos_of_char","a"):"C3S5-first-pos",
("utils/resolver.py::get_last_pos_of_char","a"):"C6S2-last-pos",
("utils/resolver.py::split_unescaped","b"):"C7S1-split-unescaped",
("utils/resolver.py::is_glob_pattern","a"):"C4S7-is-glob",
("utils/resolver.py::_maybe_convert_stringified_dxlink","a"):"C4S6-dxlink-guard",
("utils/resolver.py::escape_folder_str","a"):"C10S1-escape-folder",
("utils/pretty_print.py::flatten_json_array","a"):"C1S4-flatten-subn",
("utils/pretty_print.py::escape_unicode_string","a"):"C10S1-escape-unicode",
("utils/pretty_print.py::format_table","a"):"C6S3-table-first-row",
("utils/pretty_print.py::format_table","b"):"C3S2-table-border",
("utils/spelling_corrector.py::_edits1","a"):"C6S2-edits1-set",
("dxlog.py::DXLogHandler.truncate_message","a"):"C4S7-truncate-guard",
("cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe","a"):"C3S4-coding-display-index",
("dx_extract_utils/filter_to_payload.py::final_payload","a"):"C8S1-final-payload-columns",
("dx_extract_utils/germline_utils.py::harmonize_germline_sql","a"):"C8S1-harmonize-columns",
("utils/__init__.py::normalize_timedelta","a"):"C4S6-timedelta-suffix",
("nextflow/nextflow_templates.py::get_nextflow_src","a"):"C10S4-nextflow-src-join",
("nextflow/nextflow_utils.py::_load_versions_manifest","a"):"C8S1-versions-manifest",
("system_requirements.py::SystemRequirementsDict.override_cluster_spec","a"):"C7S4-cluster-filter-first",
("bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range","a"):"C1S4-range-int-once",
("utils/completer.py::ListCompleter.get_matches","a"):"C1S4-listcompleter-rfind",
("utils/local_exec_utils.py::has_local_job_refs","a"):"C1S4-localrefs-bind",
("utils/__init__.py::_dict_raise_on_duplicates","a"):"C10S1-dupkeys-dict",
("utils/pathmatch.py::translate","a"):"C10S4-glob-translate-join",
("cli/output_handling.py::write_expression_output","a"):"C3S2-expr-output-set",
("cli/dataset_utilities.py::validate_cohort_ids","a"):"C7S1-cohort-ids-comprehension",
}
BLOCKED_UNITS={
 "bindings/dxfile.py::DXFile.__iter__":"inputs.py: it cannot run here: `DXFile.__iter__` calls `self.read(self._read_bufsize)` on a remote file handler; `DXFile.read` fetches the file's download URL and data from the DNAnexus API over the network (and needs `describe` for the file length), so no input can make it run without network access.",
 "bindings/dxfile.py::DXFile._write2":"inputs.py: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: DXError: This DXFile handler has not been initialized with a file ID and cannot be described)",
 "dx_extract_utils/somatic_filter_payload.py::retrieve_geno_bins":"inputs.py: it cannot run here: `retrieve_geno_bins` delegates its entire workload to `retrieve_bins(...)`, which needs a DNAnexus `project` to fetch the gene manifest data objects from the platform (network/API access); no input can avoid that lookup.",
 "dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter":"inputs.py: the inputs that run here reach only 39% of the function (lines 10, 17, 22, 29, 31, 41, 47, 50-56, 58-59, 62-69, 71-72, 75, ... never ran), so they would not measure its real work. Also no behaviour-preserving repair exists inside this unit: the converter is an opaque callable, and the quadratic accumulation is created in validate_cohort_ids.",
}
NOINPUT_MSG={
 ("cli/dataset_utilities.py::validate_cohort_ids","a"):"inputs.py: it cannot run here: `validate_cohort_ids` performs its work by calling `raw_api_call`, which issues a live HTTP POST to a Vizserver (`dxpy.DXHTTPRequest`); the function cannot complete without network access to that remote service. A repair was written (build id_list with `[convert(b) for b in ids]` where `convert` is int, float or str, keeping the returned lambda) but could not be measured.",
}
used=set()
out=[]
for l in open(REPO+"step2.jsonl"):
    r=json.loads(l); suf=r['unit'].replace(P,'')
    oc=[]
    for d in r['decisions']:
        if d['verdict']!='accepted': continue
        key=(suf,d['label'])
        sid=SUBMAP.get(key)
        if sid and sid in subs:
            st=(subs[sid].get('agent_measurement') or {}).get('status')
            if st in ('no_inputs','error'):
                oc.append({"label":d['label'],"outcome":"blocked","submission":None,"why":(subs[sid]['agent_measurement'].get('reason') or NOINPUT_MSG.get(key,''))})
                used.add(sid+":blocked")
            elif st=='over_limit' and sid in ('C7S1-cohort-ids-comprehension','C3S2-expr-output-set'):
                msg = NOINPUT_MSG.get(key) or "inputs.py: no inputs could be generated for src/python/dxpy/cli/output_handling.py::write_expression_output: the generator failed: BrokenPipeError: [Errno 32] Broken pipe (three attempts). A repair was written (build `expected_columns = set(COLUMN_NAMES)` once and compare each row's key set with it) as submission C3S2-expr-output-set, which verify.py did not measure."
                oc.append({"label":d['label'],"outcome":"blocked","submission":None,"why":msg}); used.add(sid+":blocked")
            elif st=='over_limit':
                oc.append({"label":d['label'],"outcome":"deferred","submission":None,"why":"outside the 20 repairs measured (verify.py reported over_limit); repair written as submission %s" % sid})
                used.add(sid+":deferred")
            else:
                oc.append({"label":d['label'],"outcome":"submitted","submission":sid,"why":None}); used.add(sid)
        elif suf in BLOCKED_UNITS:
            oc.append({"label":d['label'],"outcome":"blocked","submission":None,"why":BLOCKED_UNITS[suf]})
        else:
            oc.append({"label":d['label'],"outcome":"deferred","submission":None,"why":"accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)"})
    if oc: out.append({"step":3,"unit":r['unit'],"outcomes":oc})
with open(REPO+"step3.jsonl","w") as f:
    for o in out: f.write(json.dumps(o)+"\n")
print(len(out), sum(len(o['outcomes']) for o in out), [u for u in used if ':' in u])
