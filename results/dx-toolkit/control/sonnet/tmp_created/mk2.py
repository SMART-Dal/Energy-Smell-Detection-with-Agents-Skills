import json
s1=[json.loads(l) for l in open("step1.jsonl")]
D={}  # unit suffix -> (what, {label:(verdict,why)})
def d(suffix, what, **dec): D[suffix]=(what,dec)
A,R="accepted","rejected"
d("spelling_corrector.py::correct","suggests the closest known word to `word` by Norvig edit distance, preferring exact, then distance 1, then distance 2",
  a=(A,"same edit as `_known_edits2`.a (the distance-2 enumeration is the cost); submitted once against `_known_edits2`"))
d("spelling_corrector.py::_known_edits2","returns the members of NWORDS that are at edit distance 2 of `word`",
  a=(A,"builds ~(54n+25)^2 candidate strings and tests each for membership in a ~100-word dict; testing each known word against the ~500 distance-1 strings with a direct edit-1 predicate removes the millions of string constructions"))
d("resolver.py::get_first_pos_of_char","returns the index of the first unescaped occurrence of a char",
  a=(A,"backward scan visits every occurrence and slices a copy each time; a forward `find` loop returns at the first unescaped hit, and rfind with an end argument avoids the slice"))
d("resolver.py::get_last_pos_of_char","returns the index of the last unescaped occurrence of a char",
  a=(A,"`string[:pos].rfind(char)` allocates a copy per iteration; `string.rfind(char, 0, pos)` searches the same range without copying"))
d("resolver.py::split_unescaped","splits a string on unescaped separators, scanning from the right",
  a=(A,"each piece costs a slice `string[:lastpos]` plus a fresh scan; passing an end bound to the scanner removes k slice copies of up to n chars"))
d("resolver.py::_maybe_convert_stringified_dxlink","converts a stringified {$dnanexus_link: ...} to a path, else returns the path unchanged",
  a=(A,"every ordinary path goes through json.loads and raises JSONDecodeError, which is caught by a bare except; a leading-brace test skips the parse and the exception for strings that cannot be JSON objects"))
d("resolver.py::resolve_path","parses a path into (project, folder, name), calling resolver helpers",
  a=(A,"`get_last_pos_of_char(':', path)` at the elif repeats the scan already stored in `last_colon`; replace by the variable"))
d("pretty_print.py::escape_unicode_string","escapes control characters and backslash in one cell string",
  a=(A,"re.sub with a string pattern and a nested function per call; a precompiled search that returns the input unchanged when no escapable char is present avoids building the replacer and the substitution for the common case"))
d("pretty_print.py::format_table","renders a table of rows as a bordered, padded text table",
  a=(A,"`len(list(table)[0])` copies the whole row list to read one row; `len(next(iter(table)))` reads it directly"),
  b=(R,"the cost is inside escape_unicode_string, whose own repair covers it; editing here would be the same reason twice"),
  c=(R,"`' '*n` padding vs ljust is a constant-factor tie; no mechanism"))
d("pretty_print.py::flatten_json_array","collapses multi-line JSON arrays of a given name onto one line",
  a=(A,"each pass of the while loop joins one line per array and rescans the document; a single regex pass whose callback joins all comma-terminated lines removes the repeated full-document scans"))
d("dxlog.py::DXLogHandler.truncate_message","truncates a log message so its JSON encoding fits a datagram",
  a=(A,"`message.encode` runs before the early return, so every message that fits pays a copy it never uses"),
  b=(A,"the loop drops one byte and re-serialises the prefix on each pass (up to 8000 json.dumps of 8 KB for escape-heavy text); the encoded length is monotone in the prefix length so a binary search finds the same cut with ~13 serialisations"))
d("cohort_filter_payload.py::generate_pheno_filter","merges a list of ids into an existing pheno filter of a cohort",
  a=(A,"`reduce(lambda a, b: a + [conv(b)], ...)` builds a new list per element: O(n^2). Calling the same lambda as `f([], b)[0]` per element yields the same converted value in O(n)"))
d("dataset_utilities.py::validate_cohort_ids","converts and validates cohort ids against the dataset via a viz query",
  a=(A,"same quadratic reduce over the user's id list; the same per-element `f([], b)[0]` comprehension gives an identical list"))
d("dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe","builds the coding dictionary DataFrame for one coding",
  a=(A,"`display.index(c)` and `c in display` scan a list per code; a position dict built once makes each lookup O(1), keeping first-occurrence semantics via setdefault"),
  b=(A,"each recursion level re-yields the child's tuples, so a node at depth d is passed through d generator frames; threading a result list through the recursion appends each tuple once"))
d("dataset_utilities.py::DXDatasetDictionary.load_data_dictionary","assembles entity, edge and coding frames of the data dictionary",
  a=(A,"`source_eblock.assign(...)` copies the entire entity DataFrame per edge and the copy is discarded; the dictionary is updated through `.values` aliasing before it, so deleting the statement changes nothing observable"))
d("dataset_utilities.py::extract_assay_expression","queries expression data of an assay and writes it out (network)",
  a=(A,"`DATASET_DESCRIPTOR` is assigned and never read; each access of descriptor_file_dict downloads, gunzips and parses the descriptor, so deleting the line removes a whole download"),
  b=(A,"`assays_info_dict['molecular_expression']` and `assay_names_list` each re-download the descriptor on every evaluation; evaluating once into locals saves 2-3 downloads"),
  c=(A,"`set(additional_fields)` is rebuilt for every schema column inside the comprehension"))
d("dataset_utilities.py::extract_assay_germline","extracts germline variant data of an assay (network)",
  a=(A,"with infer flags and a genotype_type filter that excludes the inferred type, two API queries and an O(loci*samples) list are produced and then filtered out; guard the block"))
d("dataset_utilities.py::get_codings","fetches coding pages from the viz server and merges them (network)",
  a=(A,"deepcopy of a freshly parsed response page that nothing else aliases; storing the page directly avoids the duplicate"))
d("retrieve_bins.py::retrieve_bins","looks up genomic bins for genes from a manifest on the platform (network)",
  a=(A,"each call spawns `dx cat` and downloads and parses the full gene manifest; reading through dxpy in process and avoiding the existence-probe describe removes a process spawn per call"))
d("filter_to_payload.py::validate_JSON","validates a user JSON filter",
  a=(A,"opens and parses a schema file whose result is never used (validate() is commented out); drop the read"))
d("filter_to_payload.py::final_payload","builds the final extract payload and field list",
  a=(R,"avoiding the re-read needs a module-level cache and a defensive copy because the caller appends to the returned list; the saving is one small file open per call"),
  b=(R,"two passes over a list of a dozen fields; negligible"))
d("germline_utils.py::harmonize_germline_sql","rewrites a genotype-only SQL statement to match the union columns",
  a=(R,"the fix is a module-level cache which a function-only edit cannot introduce; the file is small and read at most twice per run"))
d("germline_utils.py::harmonize_germline_results","pads each result row to the full field list with None",
  a=(A,"two membership tests and two assignments per field per row; a dict comprehension with `.get` does one lookup per field inside the interpreter's comprehension loop"))
d("germline_utils.py::infer_genotype_type","adds inferred ref/no-call entries for samples missing at each locus",
  a=(A,"`loci_dict[locus]` is looked up three times per sample in the inner loop; bind it and the sample set once per locus"))
d("germline_utils.py::filter_results","removes entries whose key value is in a restricted list",
  a=(R,"restricted_values holds at most a few strings, where a list scan beats building a set; and values may be unhashable"))
d("output_handling.py::write_expression_output","writes expression rows as CSV to a file or stdout",
  a=(A,"`set(COLUMN_NAMES)` and `set(i.keys())` are built for every row, O(rows*cols) allocation; build the expected set once and compare key views"))
d("dxfile.py::DXFile._write2","buffers data and dispatches upload parts",
  a=(A,"for data longer than the buffer each recursion slices `data[remaining_space:]`, copying the whole tail every time (O(L^2/B)); a loop over offsets copies each byte once"))
d("dxfile.py::DXFile._read2","reads a byte range using prefetched chunks",
  a=(A,"each chunk is sliced and written to a growing BytesIO and copied again by buf.read(); collecting pieces and joining once removes the extra copies (network unit: needs a download iterator)"))
d("dxfile.py::DXFile.read","reads from the file, checking project membership first",
  a=(R,"merging the existence probe with the size describe changes which request fails with which exception and needs a new code path; not a small edit"))
d("nextflow_templates.py::get_nextflow_src","renders the nextflow.sh template with per-input parameters",
  a=(A,"two strings are extended with `+=`/`+` once per custom input, copying the accumulated text each time; a list joined once is linear"))
d("nextflow_builder.py::prepare_custom_inputs","turns nextflow_schema.json properties into dx inputs",
  a=(R,"step-1 suspicion bundled three reasons; split into b, c, d on the second reading"),
  b=(A,"`property_key in required_inputs` scans a list per property; a set makes it one hash lookup"),
  c=(A,"`inputs.insert(0, x)` is O(n) per required input; collecting required inputs in order and reversing once gives the same final order"),
  d=(R,"two small dicts built per property is a micro-cost with no way to hoist except nested-scope changes; dominated by the JSON load"))
d("describe.py::format_currency","formats a currency value using locale",
  a=(A,"`locale.setlocale` re-reads and re-applies the locale on every call; checking the current setting first and skipping the call when equal leaves identical process state"))
d("describe.py::print_project_desc","prints a project description field by field",
  a=(R,"turning the list into a set inside the function costs as much to build as it saves; a module-level constant is outside a function-only edit"))
d("compat.py::md5_hasher","creates an md5 hasher compatible with FIPS",
  a=(R,"on Python 3.9+ (this venv is 3.10) `usedforsecurity` is accepted and no exception is raised, so there is no waste to remove"))
d("dx.py::find_executions","lists executions and prints them as a tree (network)",
  a=(A,"`x not in executions_by_parent[parent]` scans a list per insert, O(k^2) for k children; tracking membership in a set keeps the list order"),
  b=(R,"emptiness test on a key list, negligible"),
  c=(R,"deep execution trees are rare and the dict copy is dominated by printing"))
d("dx.py::generate_batch_inputs","expands batch patterns via the API and writes TSV files (network)",
  a=(A,"flatten_batch sorts `b['inputs'].items()` twice per row, and `sorted(...)` of the same keys is already in `input_names`; build each row once from input_names"))
d("dx.py::get_database","resolves a database file listing for download (network)",
  a=(A,"debug strings are formatted eagerly, including the full folder listing, although the DEBUG level is never enabled (basicConfig INFO); guard formatting with isEnabledFor"))
d("dx.py::run_body","prepares and launches `dx run` (network)",
  a=(A,"deepcopy of the whole cloned job description to read one key"),
  b=(A,"one describe round trip per workflow stage even when stages share an executable; memoise by executable id"))
d("dx.py::watch","streams job logs with timestamps (network)",
  a=(A,"enrich_msg formats a datetime string and curses colour for every message even when timestamps are off; compute lazily"))
d("dx.py::ssh","connects to a job by ssh (network)",
  a=(A,"describe every second while a job is queued; capped backoff cuts requests and wakeups"),
  b=(A,"describe after the ssh session whose result is only read when check_running; move it inside the condition"))
d("dx.py::archive","requests archival of files (network)",
  a=(A,"one full-describe find_data_objects per path; request only name/id fields"),
  b=(A,"deepcopy where a shallow copy suffices because only a top-level key is added"))
d("dx.py::cd","changes the working directory in the CLI (network)",
  a=(A,"project describe at the top is used in one branch only; move it into the branch"))
d("search.py::_find","pages through an API find method as a generator",
  a=(A,"after yielding exactly `limit` results the code requests the next page, which is thrown away on the next iteration; return right after the last wanted result"))
d("dxdatabase_functions.py::_download_dxdatabasefile","downloads a database file in chunks (network)",
  a=(A,"md5 hasher updated over every byte of every chunk but never checked, since verify_part calls are commented out"),
  b=(A,"describe call whose result variable is never read afterwards"))
d("dxdatabase.py::DXDatabase.get_download_url","returns (and caches) a download URL (network)",
  a=(A,"the existence describe runs before the cache check on every chunk request; DXFile runs it only on a cache miss"))
d("executable_unbuilder.py::_dump_app_or_applet","downloads app resources and writes source (network)",
  a=(A,"getmembers() decompresses the whole archive up front and each extract then seeks backwards in the gzip stream; iterating the archive lazily extracts in one pass"))
d("config.py::DXConfig.get_session_conf_dir","finds/creates the session config dir and cleans stale ones",
  a=(R,"the cleanup is requested by the caller via an argument and creates observable file removals; throttling it changes the unit's effect on the filesystem"))
d("job_log_client.py::metrics_top","curses top-like view of job metrics",
  a=(R,"rate-limiting redraws changes the screen output sequence; cannot be checked for identical behaviour"))
d("dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow","returns the region's underlying workflow handler (network)",
  a=(A,"the region cache is overwritten with a single handler instead of being keyed by region, so each call re-describes; store per region"))
d("app_builder.py::upload_resources","tars resources, checks for a bundle, uploads (network)",
  a=(R,"moving the checksum pass ahead of the tar needs restructuring most of a 140-line function, not a small edit"))
d("collect_images.py::_populate_cached_file_ids","looks up cached image files on the platform (network)",
  a=(A,"one find_data_objects per image ref even when refs repeat the same image; search once per distinct key"))
d("workflow_builder.py::_assert_executable_regions_match","checks stage executables share regions (network)",
  a=(A,"describe calls are repeated for executables used by several stages; iterate distinct ids"))
d("executable_builder.py::get_valid_bill_to","validates a billTo (network)",
  a=(A,"`dxpy.whoami()` round trip precedes the branches and is unused for org billTo; move into the branch that needs it"))
d("system_requirements.py::SystemRequirementsDict.override_cluster_spec","merges requested cluster instance counts into app specs",
  a=(A,"deep-copies every entrypoint and then discards most; filter first, copy only the survivors"))
d("local_exec_utils.py::run_one_entry_point","runs a local entry point and updates job_outputs.json",
  a=(R,"the O(jobs) re-resolution is the intended propagation of finished outputs and the unit launches subprocess jobs; no small edit preserves the written file"))
d("download.py::download","downloads files/folders (network)",
  a=(A,"list_subfolders per path argument even when several share (project, parent folder); memoise per pair"))
d("cp.py::cp_to_noexistent_destination","clones objects to a new destination and renames (network)",
  a=(R,"each loop iteration makes a rename API call, which dominates the list scan"))

out=[]
for r in s1:
    key=r["unit"].split("dxpy/",1)[1]
    key=key.replace("bindings/","").replace("dx_extract_utils/","").replace("cli/","").replace("utils/","").replace("scripts/","").replace("nextflow/","").replace("apollo/","")
    # keys defined by basename::qualname
    p,q=r["unit"].split("::"); base=p.split("/")[-1]+"::"+q
    what,dec=D[base]
    decs=[]
    for s in r["suspicions"]:
        v,w=dec[s["label"]]
        decs.append({"label":s["label"],"lines":s["lines"],"verdict":v,"why":w})
    labels={x["label"] for x in r["suspicions"]}
    for k in dec:
        if k not in labels:
            v,w=dec[k]; decs.append({"label":k,"lines":r["suspicions"][0]["lines"],"verdict":v,"why":w})
    assert labels<=set(dec), base
    out.append({"step":2,"unit":r["unit"],"what_it_does":what,"decisions":decs})
assert len(out)==len(s1)
open("step2.jsonl","w").write("".join(json.dumps(o)+"\n" for o in out))
print(len(out), sum(1 for o in out for x in o["decisions"] if x["verdict"]=="accepted"))
