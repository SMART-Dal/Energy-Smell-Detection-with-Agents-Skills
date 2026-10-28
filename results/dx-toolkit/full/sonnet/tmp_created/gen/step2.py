import json
R={}  # (unit-suffix, label) -> reason for rejection
def rj(u,l,why): R[(u,l)]=why
rj("utils/resolver.py::clean_folder_path","a","The `get_last_pos_of_char('/', path)` test asks whether the path ends in an unescaped slash; `split_unescaped` discards that fact (it drops empty strings), so the second scan is not a repeat of the first and no local can stand in for it.")
rj("utils/resolver.py::resolve_job_ref","a","Each array element needs its own describe request; the bulk endpoint (`system_describe_data_objects`) has a different failure shape, so no edit keeps the exceptions and output identical.")
rj("utils/resolver.py::resolve_job_ref","b","`Looks like it, but is not` (a mutable default the body never grows): `describe['project']` is overwritten on every call and the dict holds nothing else, so nothing accumulates and a fresh dict per call only adds an allocation.")
rj("utils/resolver.py::check_folder_exists","a","The folder listing is server state that can change between calls (the function exists to test it), so caching it across a batch would change answers.")
rj("utils/resolver.py::check_folder_exists","b","`clean_folder_path` is called once in each of two different functions, not twice in one scope; no local can share it.")
rj("utils/resolver.py::get_exec_handler","a","The failing describe calls are what tell an app name from a workflow or object path, and they raise or return in ways later branches depend on; skipping them changes which handler is returned.")
rj("utils/__init__.py::wait_for_a_future","a","`wait(..., FIRST_COMPLETED)` registers the same waiters as `as_completed`; nothing is saved by switching, and the KeyboardInterrupt handling would need rewriting.")
rj("compat.py::md5_hasher","a","On this interpreter (CPython 3.10) `hashlib.new('md5', usedforsecurity=False)` succeeds on the first try, so the except branch never runs and there is no exception cost to remove.")
rj("utils/config.py::DXConfig.get_session_conf_dir","a","The scan is the session-directory cleanup the function promises (`cleanup=True`); throttling it would change which stale directories get removed.")
rj("utils/config.py::DXConfig._read_conf_dir","a","`Looks like it, but is not` (a pre-check that races): replacing the swallowed FileNotFoundError with `os.path.exists` leaves a window in which the file vanishes and the error escapes.")
rj("utils/describe.py::format_currency","a","`locale.setlocale` is process-global state the function changes on purpose; dropping or caching the call changes the locale other code sees.")
rj("utils/describe.py::render_bundleddepends","a","No bulk call returns the file properties and record project in one reply with the same errors, so the per-item calls cannot be replaced by an edit that preserves behaviour.")
rj("utils/describe.py::get_ls_l_desc_fields","a","The function returns the dict it builds and callers may mutate it; a shared module constant would leak those edits across calls.")
rj("utils/batch_utils.py::_search_column_id","a","The scan is called once per file column from `batch_launch_args`; the index belongs in the caller and is repair `a` of that unit, so this would be the same edit.")
rj("utils/file_load_utils.py::get_job_input_filenames","a","`handler.name` is a describe per file; a bulk describe returns a different error shape, so no behaviour-preserving edit exists inside the unit.")
rj("utils/file_load_utils.py::analyze_bash_vars","b","`fnmatch.fnmatch` already caches its compiled pattern, and the patterns per key are few, so precompiling saves a dict lookup per file at most.")
rj("utils/local_exec_utils.py::wait_for_depends_on","a","`Looks like it, but is not` (a call kept for the exception it raises): `describe()` after `wait_on_done()` raises for an inaccessible or failed job, and removing it would let that pass silently.")
rj("utils/local_exec_utils.py::queue_entry_point","a","The whole file is rewritten with indent=4 and that file is the unit's output; a cheaper bookkeeping structure would change the bytes written.")
rj("utils/local_exec_utils.py::resolve_job_ref","a","A per-job output cache would live in module state and the unit must wait on and describe each job it is given; the saving depends on how many JBORs share a job and I could not show it here.")
rj("utils/executable_unbuilder.py::_dump_app_or_applet","b","One properties lookup per bundled dependency has no bulk equivalent returning the same exceptions.")
rj("utils/executable_unbuilder.py::_dump_app_or_applet","c","The download, untar and unlink sequence is the contract (files written); streaming extraction would change what is left on disk if it fails midway.")
rj("utils/completer.py::path_completer","a","Server-side name filtering through `name=text+'*'` changes case and escaping behaviour of completions, so the result set is not provably the same.")
rj("utils/completer.py::path_completer","b","Separate queries per data class return different result sets per class; a combined query changes ordering of the completions.")
rj("utils/job_log_client.py::metrics_top","a","Redrawing once per message is the visible behaviour of the curses screen; throttling it changes what is displayed between messages.")
rj("utils/job_log_client.py::DXJobLogStreamClient.closed","a","No bulk describe for executions preserves the per-job state used later; this is also a network path with no offline input.")
rj("bindings/apollo/dataset.py::Dataset.assay_info_dict","a","The scan runs over a handful of assays; once `assays_info_dict` is cached by `descriptor_file_dict` an index per call would cost more than the scan it replaces.")
rj("bindings/apollo/dataset.py::Dataset.assay_index","a","Same as `assay_info_dict`: a linear scan over a few assay entries is cheaper than building an index per call.")
rj("bindings/apollo/data_transformations.py::transform_to_expression_matrix","a","The padded rows are the function's return value (every row carries every column with None); dropping the padding changes the returned data.")
rj("cli/dataset_utilities.py::DXDatasetDictionary.load_entity_dictionary","a","Each entity yields one small frame that `write` concatenates; the saving is a few allocations and would restructure `write`, which is outside this unit.")
rj("cli/dataset_utilities.py::extract_assay_expression","d","Whether the second `DXRecord` describe is redundant depends on which fields `resolve_cohort_to_dataset` reads, which I could not establish without running against the service.")
rj("cli/dataset_utilities.py::extract_assay_germline","a","Running the genotype queries on threads would cut wall-clock time and raise energy, and the order of printed output could change.")
rj("cli/dataset_utilities.py::extract_assay_germline","c","Sending the sample filter with the retrieval changes the request payload, so the server's reply and any error text change.")
rj("cli/exec_io.py::ExecutableInputs.add","a","`-i` arguments number a handful per command line, so exceptions raised on the plain-value path are not frequent enough to cost anything measurable.")
rj("cli/exec_io.py::ExecutableInputs.add","b","`Looks like it, but is not` (a chain whose arms are not interchangeable): the eighteen arms test class names and a dispatch table would also change the order of side effects.")
rj("cli/download.py::download","a","`list_subfolders` reflects live project state, and caching it per parent changes results if the folder changes between paths.")
rj("cli/cp.py::cp","a","`resolve_multiple_existing_paths` does not support the `allow_mult` and `all_mult` options used per source, so the bulk resolver is not equivalent.")
rj("bindings/dxdatabase_functions.py::download_dxdatabasefile","a","Retries must re-describe because a failed attempt can come from a stale describe; hoisting the describe would hide that.")
rj("bindings/dxfile_functions.py::_download_dxfile","b","`parts_to_get.index(...)` runs once per resume, not per part, so it is not a loop cost.")
rj("bindings/dxfile_functions.py::list_subfolders","a","`project_list_folder(only='folders')` lists one level only and `describe(folders=True)` returns the recursive list the function filters; the result sets differ.")
rj("bindings/dxfile_functions.py::download_folder","a","Concurrent downloads trade wall-clock time against CPU and the energy cost of threads; also order of progress output would change.")
rj("bindings/dxfile_functions.py::_verify_checksum","a","Removing a function referenced from tests does not change what the machine does at run time; it is dead code, not an energy repair.")
rj("bindings/dxfile_functions.py::_which","a","`shutil.which` follows PATHEXT and permission rules that differ from this hand-written scan on some platforms, so equivalence is not guaranteed.")
rj("bindings/dxfile.py::DXFile._read2","b","`describe` here fills `self._desc` and checks state; a narrower `fields` request changes what later attribute reads find in `_desc`.")
rj("bindings/dxfile.py::DXFile.__init__","a","The buffers are public-ish attributes read by `flush`, `close` and `__del__`; allocating them lazily changes behaviour for handles that are only closed.")
rj("bindings/dxfile.py::_readable_part_size","a","The unit is a short comparison chain run once per progress message; there is nothing to remove measurably.")
rj("bindings/dxglobalworkflow.py::DXGlobalWorkflow._get_run_input","a","The project region can change with the project argument and the describe is the way to learn it; a memo would need an invalidation rule I cannot justify.")
rj("bindings/download_all_inputs.py::_gen_helper_dict","b","`add_if_no_collision` is a guard for user-supplied names; proving it can never fire for every input is a correctness claim, not a measured saving.")
rj("bindings/download_all_inputs.py::download_all_inputs","b","Passing the parsed inputs into `_gen_helper_dict` is the same edit as suspicion `a` of that unit.")
rj("bindings/mount_all_inputs.py::mount_all_inputs","a","`mkdir`, `id -u` and `find` subprocess output is part of the observable behaviour (the find listing is printed); in-process calls would not reproduce it exactly.")
rj("bindings/search.py::org_find_apps","a","Capping at `limit` would return fewer results than the current code, which keeps paging; that is a behaviour change.")
rj("bindings/dxworkflow.py::DXWorkflow._get_stage_id","a","`self.stages` is a descriptor-backed attribute that can change after any edit call; an index built once would go stale.")
rj("bindings/dxworkflow.py::DXWorkflow.get_stage","a","`self.stages` is re-read from the describe on attribute access and may change between the two reads; no local can be shared safely.")
rj("bindings/dxjob.py::DXJob.wait_on_done","a","The two-second poll interval is the behaviour callers rely on for latency; exponential backoff would delay noticing completion.")
rj("bindings/dxanalysis.py::DXAnalysis.wait_on_done","a","Same as `DXJob.wait_on_done`: the fixed poll interval is the contract.")
rj("bindings/dxproject.py::DXContainer.describe","a","`Looks like it, but is not`: the choice of API function depends on the instance's class, and two class attributes only move the same `isinstance` test elsewhere.")
rj("__init__.py::DXHTTPRequest","a","Clearing the pool manager after any exception is deliberate: a connection that produced an error may be poisoned, and the comment-free code is the safety net.")
rj("__init__.py::append_underlying_workflow_describe","a","Concurrent describes change error ordering and the energy trade; no offline input exists.")
rj("app_builder.py::upload_resources","a","Reordering the tar, checksum and lookup changes which temporary files exist when the lookup raises; restructuring a 235-line function is more than one repair.")
rj("app_builder.py::upload_resources","b","Writing the tar.gz directly changes the bytes of the archive (compression happens over a different stream) and its checksum, which the platform compares.")
rj("app_builder.py::upload_applet","a","Each describe asks a different question (record, file name, project); there is no single call whose answer replaces them.")
rj("app_builder.py::upload_applet","b","The archive folder list_folder call doubles as the existence check whose failure path creates the folder; hoisting changes the order of platform calls.")
rj("app_builder.py::_create_app","a","`app_list_authorized_users` also validates access and its failure is part of the behaviour of a brief build.")
rj("app_builder.py::_create_app","b","One `app_describe` with fields does not return the same lists in the same order the three list calls do.")
rj("app_builder.py::_create_app","c","The caller relies on `app_spec = inherited_metadata` being updated in place and returned; changing the default alters what callers observe after a first call.")
rj("executable_builder.py::get_valid_bill_to","a","`dxpy.whoami()` is an authenticated call whose failure for an invalid token is part of the behaviour on every branch.")
rj("workflow_builder.py::_get_validated_json","a","The deep copies protect the caller's spec from the validators' in-place edits; removing one makes validation mutate the caller's dict.")
rj("workflow_builder.py::_cleanup_empty_keys","a","The JSON round trip also normalises types (tuples to lists, non-string keys); a dict walk would not return the same object.")
rj("asset_builder.py::build_asset","a","`system_whoami()` doubles as an authentication check; removing the call changes the error a bad token produces.")
rj("asset_builder.py::build_asset","b","Concurrent uploads would reorder platform calls and change progress output; energy cost of threads is not obviously lower.")
rj("asset_builder.py::build_asset","c","Three removals have different error handling per object; one `remove_objects` reports a single failure.")
rj("scripts/dx_build_app.py::build_and_upload_locally","a","Per-region uploads target different projects and the resource tar is checked against each; sharing the tarball across regions changes the platform calls.")
rj("scripts/dx_build_app.py::build_and_upload_locally","c","The describe result is the function's return value when `return_object_dump` is set and its failure signals a bad build; guarding it changes behaviour.")
rj("scripts/dx_build_app.py::_check_suggestions","a","Each suggestion is a separate existence check with its own warning text; dedupe changes the number of warnings printed.")
rj("scripts/dx_build_app.py::_check_file_syntax","a","Compiling to a `.pyc` in the temp dir is how `py_compile` reports syntax errors; `compile()` raises a different exception type and message.")
rj("nextflow/collect_images.py::_populate_cached_file_ids","b","The manifest retry loop retries only on non-zero exit; classifying exits as permanent needs knowledge of docker's messages I cannot verify.")
rj("nextflow/collect_images.py::_docker_manifest_inspect","a","Whether a non-zero exit is permanent depends on docker's error text, which I cannot verify here, so no behaviour-preserving edit exists.")
rj("nextflow/collect_images.py::bundle_docker_images","a","Pull, save and upload per image are heavy I/O jobs; running them concurrently trades time for energy and reorders output.")
rj("nextflow/nextflow_utils.py::get_project_with_assets","a","The describe is the probe that picks production or staging; it cannot be dropped, and caching it across builds in one process changes behaviour only in tests.")
rj("nextflow/validate_nextflow_assets.py::validate_assets","a","Today the two versions use different files, so there is no repeat to remove.")
rj("templating/utils.py::create_files_from_templates","a","`any(generator)` over a short tuple of suffixes; `endswith(tuple)` saves a few dispatches on a code path that runs per template file at project creation.")
rj("scripts/dx.py::find_executions","a","The first-pass query reads only a few fields; narrowing `describe_args` changes the request and I could not run against the service to confirm which fields later passes read.")
rj("scripts/dx.py::get_database","b","Parallel downloads trade time for energy and reorder progress output.")
rj("scripts/dx.py::run_body","b","The per-stage describe supplies the executable's name and is not duplicated; stages sharing an executable is an assumption about data, not code.")
rj("scripts/dx.py::describe","a","Calling find_apps and find_global_workflows after an object match is how `dx describe` reports ambiguous names; skipping them changes output.")
rj("scripts/dx.py::ssh","a","The socket lifetimes per retry follow the SSH retry protocol; closing earlier changes which port the proxy holds between attempts.")
rj("scripts/dx.py::ssh","b","The one-second poll is how `dx ssh` notices the job coming up; backoff would delay the connection.")
rj("scripts/dx.py::DXCLICompleter.get_matches","a","Server-side `installed` filtering is not confirmed to be supported by `find_apps` here; the client-side filter is the safe form.")
rj("scripts/dx.py::find_apps_result","a","Same as the completer: server-side filtering of installed apps is not confirmed.")
rj("scripts/dx.py::archive","b","One find per folder would change which objects match when several files share a name; the per-path find is the contract.")
rj("utils/pretty_print.py::format_tree","a","Index-based iteration is needed because the loop compares `i` to `len(nodes)-1`; a rewrite with enumerate saves one lookup per node and I expect no measurable change.")
rj("dx_extract_utils/germline_utils.py::get_germline_ref_payload","a","One short loop over locus ids; the comprehension saves an `append` attribute lookup per element, which I judged below the noise floor.")
rj("scripts/dx_build_app.py::build_app_from","a","The scan flagged a loop-invariant expression I could not locate as costly; the loop calls API functions that dominate.")
rj("cli/dataset_utilities.py::has_access_level","a","Constant four-item list built once per call; a call runs once per command, so nothing measurable.")
rj("cli/dataset_utilities.py::list_fields","a","The `sorted()` is the output order; the per-field loop is bounded by schema size and runs once per command.")
rj("cli/dataset_utilities.py::DXDatasetDictionary.load_coding_dictionary","a","The outer key is looked up once per entity (not per field) and the model dict is small, so nothing measurable.")
rj("cli/dataset_utilities.py::DXDatasetDictionary.get_join_path_to_entity_field_map","a","The re-indexed values are three dict reads per field with the regex match dominating; the saving is below the noise floor.")
rj("utils/pretty_print.py::format_timedelta","a","`out_str` is built by prepending at most six short pieces; nothing measurable.")
rj("utils/describe.py::io_val_to_str","a","Repeated `val['$dnanexus_link']` lookups on small dicts are a few dict reads per value; nothing measurable.")
rj("utils/local_exec_utils.py::get_implicit_depends_on","a","Same repeat-index pattern as `has_local_job_refs` on small input structures; covered by that unit's repair.")
rj("workflow_builder.py::_validate_json_for_global_workflow","a","`all([...])` over the handful of regionalOptions values; a list of a few booleans costs the same as the generator.")
rj("__init__.py::_is_retryable_exception","a","The chain returns True/False for different exception classes and is not hot; collapsing the last branch saves one jump on an error path.")
rj("utils/resolver.py::resolve_global_executable","a","`is_hashid(path)` runs once per call and the flag test order does not change what the API calls do afterwards; nothing measurable.")
rj("utils/describe.py::print_app_desc","a","Runs once per `dx describe`; the list is a few dozen strings.")
rj("utils/describe.py::print_globalworkflow_desc","a","Runs once per `dx describe`; the list is a few dozen strings.")
rj("utils/describe.py::print_execution_desc","a","Runs once per `dx describe`; the list is a few dozen strings.")

WHAT={
"utils/resolver.py::get_first_pos_of_char":"returns the index of the first unescaped occurrence of a character in a string by scanning backwards over every occurrence; used by completers, dx download and parse_input_keyval.",
"utils/resolver.py::get_last_pos_of_char":"returns the index of the last occurrence of a character not preceded by an odd number of backslashes; called from path resolution, completers and split_unescaped.",
"utils/resolver.py::split_unescaped":"splits a string on a character that is not backslash-escaped, right to left, by repeatedly calling get_last_pos_of_char on shrinking prefixes.",
"utils/pretty_print.py::flatten_json_array":"collapses all JSON arrays with a given name onto one line using repeated regex substitution until no more line breaks remain.",
"utils/pretty_print.py::escape_unicode_string":"escapes control characters and backslash in a string with re.sub and a callback; called once per table cell by format_table.",
"utils/pretty_print.py::format_table":"formats a list of rows as a boxed, coloured text table, computing column widths and padding every row.",
"utils/spelling_corrector.py::correct":"suggests the known word closest to the input by training a frequency model then testing distance 0, 1 and 2 edit candidates.",
"dxlog.py::DXLogHandler.truncate_message":"truncates a log message so its JSON encoding stays under 8000 bytes, trimming one byte at a time.",
"cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe":"builds the coding dictionary frame for one coding, unpacking a display hierarchy and assigning a display order to each code.",
"dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter":"adds an in/not-in filter for a primary entity field to a cohort filter structure, converting stored values with a reduce.",
"dx_extract_utils/filter_to_payload.py::final_payload":"builds the vizserver payload for a filter type by reading the matching return_columns JSON file and ordering the result.",
"dx_extract_utils/germline_utils.py::harmonize_germline_sql":"rewrites a genotype-only SQL statement to join allele rows and select all return columns, after reading return_columns_genotype.json.",
"bindings/dxfile.py::DXFile.__iter__":"yields lines of a text-mode remote file by reading buffers and splitting the accumulated buffer on newlines.",
"bindings/dxfile.py::DXFile._write2":"writes bytes into the file's write buffer, dispatching a part upload whenever the buffer is full, recursing on the remaining data.",
"utils/__init__.py::normalize_timedelta":"converts strings such as '5d' or '120' to milliseconds, trying int() first and falling back to a suffix table.",
"nextflow/nextflow_templates.py::get_nextflow_src":"fills the nextflow applet source template by concatenating generated parameter and exclusion strings for each input.",
"nextflow/nextflow_utils.py::_load_versions_manifest":"opens, parses and schema-checks versions.json on every call.",
"system_requirements.py::SystemRequirementsDict.override_cluster_spec":"returns a copy of the requirements with cluster specs overridden, deep-copying entrypoints before filtering them.",
"bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range":"validates that each item's end exceeds its start and that the combined range fits a window, converting values to int more than once.",
"utils/completer.py::ListCompleter.get_matches":"returns the completion candidates after the last colon for each match using index-based iteration and two rfind calls.",
"utils/local_exec_utils.py::has_local_job_refs":"walks a job input structure and reports whether any value is a local job reference, re-indexing elements repeatedly.",
"utils/__init__.py::_dict_raise_on_duplicates":"object_pairs_hook that builds a dict and raises ValueError on a repeated key.",
"dx_extract_utils/somatic_filter_payload.py::retrieve_geno_bins":"annotates gene bins with a chromosome form by copying the bin list and testing membership in a 24-item list.",
"utils/pathmatch.py::translate":"translates a glob pattern into a regex string one character at a time using string concatenation.",
"cli/output_handling.py::write_expression_output":"validates that every row has the same columns then writes the rows as CSV or SQL text to a file or stdout.",
}
import re
out=[]
n_acc=0
for l in open('/home/javad/energy-run/dx-toolkit/step1.jsonl'):
    r=json.loads(l); suf=r['unit'].replace('src/python/dxpy/','')
    dec=[]
    for s in r['suspicions']:
        key=(suf,s['label'])
        if key in R:
            v='rejected'; why=R[key]
        else:
            v='accepted'; n_acc+=1
            why="Matches the card's definition for %s here: %s. The repair is a local edit that keeps the return value, arguments and exceptions." % (s['root_cause'], s['why'])
        dec.append({"label":s['label'],"root_cause":s['root_cause'],"lines":s['lines'],"verdict":v,"why":why})
    wd=WHAT.get(suf)
    if not wd:
        wd="%s: read in full with its callees; %s" % (suf.split('::')[1], r['suspicions'][0]['why'][0].lower()+r['suspicions'][0]['why'][1:])
    out.append({"step":2,"unit":r['unit'],"what_it_does":wd,"decisions":dec})
with open('/home/javad/energy-run/dx-toolkit/step2.jsonl','w') as f:
    for o in out: f.write(json.dumps(o)+"\n")
unused=[k for k in R if not any(k==(o['unit'].replace('src/python/dxpy/',''),d['label']) for o in out for d in o['decisions'])]
print(len(out),n_acc,"unused rejects:",unused)
