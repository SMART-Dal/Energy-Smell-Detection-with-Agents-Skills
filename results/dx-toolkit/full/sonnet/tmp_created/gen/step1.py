import json
P="src/python/dxpy/"
U=[]
def u(path, qn, *s):
    sus=[]
    for i,(rc,lines,why) in enumerate(s):
        sus.append({"label":"abcdefghij"[i],"root_cause":rc,"lines":lines,"why":why})
    U.append({"step":1,"unit":P+path+"::"+qn,"suspicions":sus})

# ---- utils/resolver.py
u("utils/resolver.py","get_first_pos_of_char",
  ("C3.S5",[280,293],"scans every occurrence from the right with `string[:pos].rfind(char)` (a slice copy each pass) to keep the leftmost unescaped one; a forward `str.find` could stop at the first unescaped hit"),
  ("C6.S2",[283],"`string[:pos].rfind(char)` copies a prefix per iteration; `string.rfind(char, 0, pos)` copies nothing"))
u("utils/resolver.py","get_last_pos_of_char",
  ("C6.S2",[253,257],"`string[:pos].rfind(char)` allocates a slice per loop pass; `string.rfind(char, 0, pos)` avoids it"))
u("utils/resolver.py","split_unescaped",
  ("C6.S2",[309,310,311,312],"calls `get_last_pos_of_char(char, string[:lastpos])` per token: one slice per token here and another inside the callee"),
  ("C7.S1",[298,321],"repeated right-to-left rescans with slicing make the split O(n*k); one forward pass with a backslash parity count is O(n)"))
u("utils/resolver.py","is_glob_pattern",
  ("C4.S7",[177,178],"runs two escape-aware backwards scans (`*`, then `?`) with no cheap guard for strings that contain neither"))
u("utils/resolver.py","is_container_id",
  ("C4.S1",[159,160],"runs the hash-id regex before the cheap `startswith` that usually decides"))
u("utils/resolver.py","_maybe_convert_stringified_dxlink",
  ("C4.S6",[412,424],"`json.loads` is tried on every path and raises/swallows ValueError for almost all inputs; a `startswith('{')` guard would skip it"))
u("utils/resolver.py","escape_folder_str",
  ("C10.S1",[225,226],"`re.sub` with a Python callback per special char; a `str.translate` table does it in C"))
u("utils/resolver.py","resolve_path",
  ("C1.S4",[515,535],"`get_last_pos_of_char(':', path)` is computed at 515 and again at 535, and `split_unescaped` scans a third time"))
u("utils/resolver.py","clean_folder_path",
  ("C1.S4",[345],"`get_last_pos_of_char('/', path)` re-scans the path after `split_unescaped` already walked it"))
u("utils/resolver.py","parse_input_keyval",
  ("C3.S5",[1362,1365],"locates the first `=` and then splits the whole string including the value with `split_unescaped` only to take element 0"))
u("utils/resolver.py","resolve_job_ref",
  ("C9.S1",[600,603],"one sequential describe request per element of an array output"),
  ("C6.S7",[566,572],"`describe={}` mutable default is written to (`describe['project'] = project`)"))
u("utils/resolver.py","resolve_container_id_or_name",
  ("C9.S2",[388],"`find_projects(describe=True)` pulls full describes where only id and level are used"))
u("utils/resolver.py","_validate_resolution_output_length",
  ("C3.S5",[819],"`any([... for ...])` builds the full list and cannot short-circuit"))
u("utils/resolver.py","check_folder_exists",
  ("C8.S4",[1112,1118,1120],"lists all subfolders of the parent to test one name; same parent re-listed for each path in a batch"),
  ("C1.S4",[1118,1120],"`clean_folder_path` result duplicated with `_resolve_folder`"))
u("utils/resolver.py","get_exec_handler",
  ("C4.S7",[1279,1280],"issues up to two failing app/global workflow describe calls even for paths that cannot be app names"))
# ---- pretty_print
u("utils/pretty_print.py","escape_unicode_string",
  ("C10.S1",[76,82],"`re.sub` with a Python callback calling `ord(matchobj.group(1))` up to three times per match, once per table cell; `str.translate` with a table does it in C"),
  ("C8.S2",[76,82],"closure `replacer` is redefined and the pattern string re-resolved through the re cache on every call"))
u("utils/pretty_print.py","flatten_json_array",
  ("C1.S4",[205,206],"`while flatten_regexp.search(result): result = flatten_regexp.sub(...)` scans the whole text twice per pass and discards the search match; `subn` returns the count"),
  ("C7.S1",[203,207],"each pass joins one more line per array, so passes grow with array length times document size"))
u("utils/pretty_print.py","format_table",
  ("C6.S3",[132],"`len(list(table)[0])` copies the entire table to read the first row"),
  ("C3.S2",[183,184,185],"`border('│')` (WHITE()+i+ENDC()) rebuilt twice per row although constant"),
  ("C3.S1",[152,157],"`range(len(row))` indexing with a per-cell `max` call"))
# ---- spelling corrector
u("utils/spelling_corrector.py","_edits1",
  ("C6.S2",[35,36,37,38,39],"builds four lists, concatenates them and then makes a set; a single set built directly avoids two copies"),
  ("C3.S2",[38],"`if b` depends only on the outer split but is tested inside the inner loop over the alphabet"))
u("utils/spelling_corrector.py","_known_edits2",
  ("C6.S3",[41,42],"materialises every edit of every edit (~1e5 strings) when only those in NWORDS are kept"))
u("utils/spelling_corrector.py","correct",
  ("C8.S1",[58],"`_train(known_words)` rebuilds the frequency model on every call for the same choice list"),
  ("C7.S1",[59],"for small `known_words`, an edit-distance test against each known word is far cheaper than generating all distance-2 edits"))
# ---- pathmatch
u("utils/pathmatch.py","translate",
  ("C10.S4",[51,80],"`res = res + ...` per pattern character"))
u("utils/pathmatch.py","filter",
  ("C8.S2",[26,37,38,39],"`import os,posixpath` executed on each call and the match loop is hand written instead of a comprehension; the cache is wiped whole at 100 entries"))
# ---- utils/__init__
u("utils/__init__.py","group_array_by_field",
  ("C1.S3",[241,242],"`if field not in item and None not in groups: groups[None] = []` is redundant because OrderedDefaultdict.__missing__ creates the list"))
u("utils/__init__.py","normalize_timedelta",
  ("C4.S6",[205,213],"`int(timedelta)` raises ValueError for every suffixed value, which is the normal case; suffix table rebuilt per call"))
u("utils/__init__.py","_dict_raise_on_duplicates",
  ("C10.S1",[263,268],"Python-level pair loop run per JSON object; `dict(pairs)` plus a length compare finds duplicates in C"))
u("utils/__init__.py","wait_for_a_future",
  ("C3.S3",[49],"creates a fresh `as_completed` generator over all futures on every call, which re-registers waiters per call"))
# ---- compat
u("compat.py","md5_hasher",
  ("C4.S6",[33,38],"try/except as feature detection on every call; raises and catches a TypeError per call where `usedforsecurity` is unsupported"))
# ---- dxlog
u("dxlog.py","DXLogHandler.truncate_message",
  ("C4.S7",[72,74],"`message.encode` and a full `json.dumps(message)` run for every record before the length test; a cheap length guard would skip both for short messages"),
  ("C7.S1",[77,78,79],"trims one byte at a time and re-decodes and re-dumps the whole buffer each time"))
u("dxlog.py","DXLogHandler.__init__",
  ("C6.S6",[47,58],"both sockets are created before the existence checks that can raise DXError, leaking them on that path"))
# ---- config
u("utils/config.py","DXConfig.clear",
  ("C1.S8",[319,322],"with reset=True each `self[var] = ...` runs `_sync_dxpy_state()` for all core variables"))
u("utils/config.py","DXConfig.get_session_conf_dir",
  ("C1.S8",[178,206],"every process start lists the session dir and checks pid_exists and ancestor chain per entry"))
u("utils/config.py","DXConfig._read_conf_dir",
  ("C4.S6",[232,237],"opens up to nine optional files and swallows FileNotFoundError"))
u("utils/config.py","DXConfig.__len__",
  ("C6.S3",[267],"builds a list just to take its length"))
# ---- describe
u("utils/describe.py","format_currency",
  ("C1.S8",[1057],"`locale.setlocale` called on every format and raises/catches locale.Error repeatedly"))
u("utils/describe.py","get_io_spec",
  ("C5.S1",[138],"`param[\"name\"] not in skip_fields` is a list scan per parameter"))
u("utils/describe.py","print_data_obj_desc",
  ("C10.S4",[788,791],"`coldescs += ...` in a loop over columns"),
  ("C5.S1",[685,687,770],"`recognized_fields` list rebuilt per call and searched linearly per key"))
u("utils/describe.py","print_project_desc",
  ("C5.S1",[411,421,538,540],"`recognized_fields` list rebuilt per call and searched linearly for every key"))
u("utils/describe.py","get_resolved_jbors",
  ("C8.S4",[289,300],"each distinct JBOR re-fetches the full job describe; several fields of one job fetch it repeatedly"))
u("utils/describe.py","render_bundleddepends",
  ("C9.S3",[321,336],"two or more sequential API calls per bundled dependency"))
u("utils/describe.py","locale_from_currency_code",
  ("C8.S2",[1015,1016],"constant dict rebuilt per call"))
u("utils/describe.py","get_ls_l_desc_fields",
  ("C8.S2",[1136,1147],"constant dict rebuilt per call"))
# ---- printing
u("utils/printing.py","fill",
  ("C3.S3",[133,138],"a new TextWrapper is built per call, and callers call once per field"))
# ---- batch_utils
u("utils/batch_utils.py","batch_launch_args",
  ("C3.S4",[153,162],"`_search_column_id` linearly scans header_line per file column"),
  ("C3.S2",[173,181],"per cell re-checks `i not in index_2_column` and re-reads the dict values; a precomputed (i, name, class) list would do"))
u("utils/batch_utils.py","_search_column_id",
  ("C5.S2",[120,124],"linear scan over the header for each file column; a name to index dict built once would answer every query"))
# ---- file_load_utils
u("utils/file_load_utils.py","filter_dict",
  ("C5.S1",[199],"`excl_keys` is a list in callers so each key test is a linear scan; also copies `list(dict_.items())`"))
u("utils/file_load_utils.py","get_job_input_filenames",
  ("C9.S3",[233,236],"`handler.name` triggers a describe per file link"),
  ("C6.S2",[262,270],"`list(job_input.items())` copies without need"))
u("utils/file_load_utils.py","analyze_bash_vars",
  ("C3.S2",[391,396],"`file_key_descs[key]` re-fetched for every entry of the same key"),
  ("C8.S1",[374,377],"fnmatch evaluated for every pattern per file; patterns could be compiled once per key"))
u("utils/file_load_utils.py","get_input_spec_patterns",
  ("C9.S2",[283,286],"two full describes to read `function`, `inputSpec`"))
# ---- exec_utils
u("utils/exec_utils.py","DXExecDependencyInstaller.generate_shellcode",
  ("C1.S6",[319,325],"apt strings and `make_pm_atoms` built on every call even for non-apt groups"))
u("utils/exec_utils.py","entry_point",
  ("C2.S1",[223,226],"wrapper only forwards *args/**kwargs while the entry-point table stores the unwrapped f"))
u("utils/exec_utils.py","parse_args_as_job_input",
  ("C1.S4",[176,183],"`ispec.get(\"type\")` evaluated up to four times in an if chain"))
u("utils/exec_utils.py","convert_handlers_to_dxlinks",
  ("C3.S1",[167],"`for i in range(len(x))` with indexed assignment"))
# ---- local_exec_utils
u("utils/local_exec_utils.py","wait_for_depends_on",
  ("C1.S5",[209,211],"`desc = handler.describe()` is an API call whose result is never used"))
u("utils/local_exec_utils.py","get_nonclosed_data_obj_link",
  ("C9.S2",[161],"full describe per data-object link just to read state"))
u("utils/local_exec_utils.py","run_one_entry_point",
  ("C3.S6",[399,403],"after each job finishes, outputs of all finished jobs are walked again, O(jobs^2) total"),
  ("C6.S2",[335],"`list(var_defs_hash.items())` copy"))
u("utils/local_exec_utils.py","queue_entry_point",
  ("C9.S2",[243,250],"parses and rewrites the whole job_outputs.json to take len() and add one entry"))
u("utils/local_exec_utils.py","has_local_job_refs",
  ("C1.S4",[50,76],"re-indexes `io_hash[field]`/`thing[i]` several times per element and uses range(len())"))
u("utils/local_exec_utils.py","resolve_job_references",
  ("C1.S4",[128,149],"re-indexes the element three to four times and uses `isinstance(a) or isinstance(b)`"))
u("utils/local_exec_utils.py","resolve_job_ref",
  ("C8.S4",[107,115],"`wait_on_done()` plus `describe()` on the same job per JBOR; no per job cache"))
u("utils/local_exec_utils.py","run_entry_points",
  ("C1.S4",[434,439],"`while has_local_job_refs(...)` re-traverses before every resolve"))
# ---- executable_unbuilder
u("utils/executable_unbuilder.py","_dump_app_or_applet",
  ("C3.S2",[235,239],"`executable._get_describe_output_keys()` called inside the per-key loop"),
  ("C9.S3",[184,195],"a handler and `get_properties()` call per bundled dependency"),
  ("C6.S2",[203,207],"each resource downloaded to a tar.gz, untarred, then deleted"),
  ("C6.S3",[176],"nested untar helper: `t.getmembers()` reads the whole archive index into memory"))
# ---- completer
u("utils/completer.py","path_completer",
  ("C9.S2",[192,195],"pulls every visible project with full describes on each Tab press then filters client-side"),
  ("C9.S1",[211,220,237,245],"one find_data_objects call per class plus a list_folder per Tab press"))
u("utils/completer.py","get_folder_matches",
  ("C1.S4",[108],"`prefix + f + '/'` built twice per element"))
u("utils/completer.py","ListCompleter.get_matches",
  ("C1.S4",[369,371],"`self.matches[i].rfind(':')` computed twice per element with range(len())"))
u("utils/completer.py","DXAppCompleter._populate_matches",
  ("C3.S6",[296,301,303],"builds the prefixed name list for all names and filters afterwards"))
u("utils/completer.py","LocalCompleter._populate_matches",
  ("C3.S3",[331,333],"imports and constructs FilesCompleter per call"))
# ---- job_log_client
u("utils/job_log_client.py","metrics_top",
  ("C1.S8",[316],"every incoming log message triggers a full curses erase and redraw; backlog replay costs one redraw per message"),
  ("C8.S1",[377,382],"static help text re-wrapped with textwrap on every refresh"))
u("utils/job_log_client.py","DXJobLogStreamClient.closed",
  ("C9.S3",[184,185],"one sequential job_describe per seen job at stream close"))
# ---- bindings
u("bindings/apollo/dataset.py","Dataset.descriptor_file_dict",
  ("C8.S2",[40,57],"every access downloads the descriptor, gunzips and parses it; other properties memoise"))
u("bindings/apollo/dataset.py","Dataset.assays_info_dict",
  ("C8.S2",[89,111],"rebuilds the full assay index on every access (descriptor re-download included)"),
  ("C8.S3",[94,95,96,97,98,99,100,101,102,106],"`assays[index]` indexed five times per loop and `model not in ...keys()`"))
u("bindings/apollo/dataset.py","Dataset.assay_names_list",
  ("C1.S4",[121,122],"`self.assays_info_dict` evaluated twice, each a descriptor download"))
u("bindings/apollo/dataset.py","Dataset.assay_info_dict",
  ("C3.S4",[113,117],"linear scan over all assays per query on a freshly rebuilt index"))
u("bindings/apollo/dataset.py","Dataset.assay_index",
  ("C3.S4",[129,134],"linear scan over all assays per query"))
u("bindings/apollo/data_transformations.py","transform_to_expression_matrix",
  ("C1.S5",[51,55],"pads every row with None for every column (rows x cols) though csv.DictWriter would write empty cells"),
  ("C6.S2",[47,51],"`sorted(list(set))` and `list(values())` extra copies"))
u("bindings/apollo/json_validation_by_schema.py","JSONValidator.are_list_items_within_range",
  ("C1.S4",[220,237,238],"each item's `int(...)` conversion runs in the loop and again in two comprehensions"),
  ("C3.S2",[227],"`check_each_separately` test is loop invariant"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.__init__",
  ("C5.S1",[39,62],"26-item `SUPPORTED_VIZSERVER_CONDITIONS` list rebuilt per instance and searched with `in`"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.parse_list_v1",
  ("C3.S2",[215,239],"per list item re-reads `key`, `keys` and the supported-condition test for every schema property though none depends on the item"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.parse_v1",
  ("C4.S4",[128,141,153],"three consecutive `if`s on `current_properties` that are exclusive"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.convert_to_between_operator",
  ("C1.S4",[383,386],"`set(operators_list)` built twice"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.build_partial_overlap_genobin_filters",
  ("C6.S1",[464,507],"four intermediate filter dicts are built then `.update`d into a pre-made structure"))
u("bindings/apollo/vizserver_filters_from_json_parser.py","JSONFiltersValidator.merge_duplicate_filters",
  ("C6.S2",[589,590],"`merged_filters[key] = []` then `.extend(conditions)` copies per key"))
u("bindings/apollo/cmd_line_options_validator.py","ArgsValidator.interpret_mutually_exclusive_group",
  ("C3.S5",[165,172],"counting loop does not stop at 2"))
u("bindings/apollo/cmd_line_options_validator.py","ArgsValidator.interpret_exclusive_with_exceptions",
  ("C4.S1",[130,137],"argument values gathered before the cheap `parser_dict.get(main_key)` test that usually decides"))
# dx_extract_utils
u("dx_extract_utils/filter_to_payload.py","final_payload",
  ("C8.S1",[236,255],"`return_columns_*.json` re-opened and parsed on every call; extract_assay_germline calls it up to four times"),
  ("C3.S5",[266,270],"loop scans all fields for sample_id without breaking on the first match"),
  ("C10.S1",[280,282],"append loop that is a list comprehension"))
u("dx_extract_utils/filter_to_payload.py","validate_JSON",
  ("C1.S5",[293,297],"schema file is opened and parsed into `json_schema`, which is never used"))
u("dx_extract_utils/filter_to_payload.py","location_filter",
  ("C3.S2",[108,131],"`\"{}$a_id\".format(table)` and the `[...][0][\"geno_bins\"]` chain re-resolved per iteration"))
u("dx_extract_utils/filter_to_payload.py","generate_assay_filter",
  ("C8.S3",[164,180],"iterates `.keys()` then indexes `full_input_dict[key]` three times"))
u("dx_extract_utils/somatic_filter_payload.py","retrieve_geno_bins",
  ("C5.S1",[58],"module-level 24-item `chrs` list searched per bin"),
  ("C6.S2",[54,61],"`updated_bins` copies a list while mutating the same dicts"))
u("dx_extract_utils/somatic_filter_payload.py","location_filter",
  ("C8.S3",[147,150,156],"nested `[\"variant_read_optimized$allele_id\"][0][\"geno_bins\"]` re-resolved each iteration; list membership on `chrs`"))
u("dx_extract_utils/somatic_filter_payload.py","basic_filter",
  ("C1.S2",[80],"`table` overwritten with a constant and never read"))
u("dx_extract_utils/somatic_filter_payload.py","generate_assay_filter",
  ("C8.S3",[187,203,204],"iterates `.keys()` and then double-indexes"))
u("dx_extract_utils/somatic_filter_payload.py","somatic_final_payload",
  ("C10.S1",[286,288],"`field_names` append loop is a comprehension"))
u("dx_extract_utils/germline_utils.py","harmonize_germline_sql",
  ("C8.S1",[126,127],"`return_columns_genotype.json` re-read and parsed per call"),
  ("C1.S4",[131,132],"the same regex run as `re.search` then again as `re.sub`"))
u("dx_extract_utils/germline_utils.py","_harmonize_sql_select_named_expression",
  ("C1.S4",[96,113,114],"SELECT_LIST_REGEX evaluated three times over the SQL"),
  ("C6.S1",[100],"`tuple(return_column)[0]` allocates a tuple per column"))
u("dx_extract_utils/germline_utils.py","harmonize_germline_results",
  ("C10.S1",[145,152],"manual double loop equals a per-row dict comprehension with `.get`"))
u("dx_extract_utils/germline_utils.py","infer_genotype_type",
  ("C3.S2",[295,305],"`loci_dict[locus][\"samples\"]` and `[\"entry\"]` re-indexed in the inner loop; final list concatenation copies"))
u("dx_extract_utils/germline_utils.py","sort_germline_variant",
  ("C8.S3",[69,78],"`float(\"inf\")` built and keys double-looked-up per sort key call"))
u("dx_extract_utils/cohort_filter_payload.py","generate_pheno_filter",
  ("C7.S1",[37,39],"`reduce(lambda a,b: a+[...], ..., [])` copies the accumulator on every step; sets rebuilt per condition"))
u("dx_extract_utils/retrieve_bins.py","retrieve_bins",
  ("C8.S4",[12,36],"two describes, a `dx cat` subprocess and a full manifest json.loads per call; once per gene key"))
u("dx_extract_utils/input_validation.py","is_list_of_strings",
  ("C3.S2",[26,37],"`python_version == 2` tested for every item"))
u("dx_extract_utils/input_validation.py","validate_filter",
  ("C4.S4",[42,107,175],"three consecutive exclusive `if filter_type ==` blocks"),
  ("C5.S1",[63],"membership tested against a list literal per item"))
u("dx_extract_utils/input_validation_somatic.py","validate_somatic_filter",
  ("C1.S4",[28,29,35,36,78,79,102,103],"`set(keys)` built twice and expected_keys converted set->list->difference"),
  ("C5.S1",[93],"16-item list searched per item"))
u("dx_extract_utils/input_validation_somatic.py","is_list_of_strings",
  ("C3.S2",[10,21],"python version check repeated per item"))
# cli
u("cli/dataset_utilities.py","validate_cohort_ids",
  ("C7.S1",[1750,1758],"`reduce(lambda a, b: a+[int(b)], ids, [])` copies the accumulator each step, quadratic in ids"),
  ("C1.S4",[1789,1793,1795],"`set(id_list)` built twice; loop fills discovered_ids one at a time"))
u("cli/dataset_utilities.py","get_assay_name_info",
  ("C1.S5",[732,733,734],"builds four full lists though only index 0 of two is used"),
  ("C6.S2",[743,744],"`list(target_assay_names)` copies a list just to test membership"),
  ("C3.S5",[758,766,776],"three loops rescan target_assays for the same name without breaking"))
u("cli/dataset_utilities.py","get_codings",
  ("C6.S2",[278],"each coding deep-copied although the page is local and discarded"))
u("cli/dataset_utilities.py","DXDatasetDictionary.create_coding_name_dframe",
  ("C3.S4",[2292,2293,2294],"`c in display` then `display.index(c)` are two linear list scans per code; a `{code: i+1}` dict built once answers both"),
  ("C1.S5",[2292,2299,2301],"display_order is computed (including the quadratic scan) and then popped when paginated"),
  ("C7.S3",[2248,2266],"recursive generator re-yields every item through each ancestor frame"))
u("cli/dataset_utilities.py","DXDatasetDictionary.load_data_dictionary",
  ("C1.S5",[2068,2070],"`source_eblock = source_eblock.assign(...)` copies the frame and the result is not used"),
  ("C3.S4",[2054,2066],"each edge recomputes a boolean mask over the source block name column"))
u("cli/dataset_utilities.py","DXDatasetDictionary.create_entity_dframe",
  ("C8.S2",[2078,2100],"`required_columns`, `extra_cols` and the type-mapping dict rebuilt per entity"))
u("cli/dataset_utilities.py","DXDatasetDictionary.load_entity_dictionary",
  ("C6.S1",[2323,2335],"one single-row DataFrame per entity then concatenated"))
u("cli/dataset_utilities.py","csv_from_json",
  ("C10.S3",[1198,1199],"Python-level `writerow` loop instead of `writerows`"),
  ("C6.S6",[1183,1201,1202],"output file opened without a context manager"))
u("cli/dataset_utilities.py","extract_dataset",
  ("C8.S3",[498,509],"`rec_descriptor.model[\"entities\"]` and nested `[\"fields\"]` re-resolved per field entry"),
  ("C1.S1",[552],"`write_ot` assigned and never used"))
u("cli/dataset_utilities.py","json_validation_function",
  ("C1.S1",[589],"`filter_arg` built and never read"))
u("cli/dataset_utilities.py","retrieve_entities",
  ("C8.S3",[1135,1140],"`model[\"entities\"][entity]` looked up three times per entity"))
u("cli/dataset_utilities.py","extract_assay_somatic",
  ("C5.S1",[1300,1303],"membership tested against a 22-item list per supplied field"))
u("cli/dataset_utilities.py","extract_assay_expression",
  ("C1.S1",[1662,1665],"`DATASET_DESCRIPTOR = dataset.descriptor_file_dict` is assigned and never read yet costs a download, gunzip and parse"),
  ("C1.S2",[1574,1593],"`filter_schema` assigned and reassigned twice"),
  ("C3.S2",[1638,1646],"`set(additional_fields)` rebuilt for every element of the comprehension"),
  ("C8.S4",[1432],"DXRecord created and described again after resolve_existing_path already returned a describe"))
u("cli/dataset_utilities.py","extract_assay_germline",
  ("C11.S5",[1067,1072,1086,1093],"independent genotype queries issued one after another"),
  ("C6.S2",[1111],"`[locus for locus in ...]` copies a list for no reason"),
  ("C9.S2",[1106,1109],"all sample ids fetched then intersected with the filter"))
u("cli/exec_io.py","ExecutableInputs.add",
  ("C4.S6",[588,592,604,619],"`json.loads` plus `raise Exception()` and unpacking failures used as the normal path for plain values"),
  ("C4.S3",[639,670],"18-branch elif chain on `input_class`; `immediate_types` rebuilt per call"))
u("cli/output_handling.py","write_expression_output",
  ("C3.S2",[126,127],"`set(COLUMN_NAMES)` and `set(i.keys())` rebuilt for every row"))
u("cli/download.py","download",
  ("C8.S4",[228],"`list_subfolders` called for every path even when it matched files; repeated for paths with the same parent"))
u("cli/download.py","_download_folders",
  ("C3.S2",[175],"loop-invariant `args.recursive` check runs only after all API calls"))
u("cli/cp.py","cp_to_noexistent_destination",
  ("C5.S1",[99,101],"`result['id'] not in exists` searches a list per result"))
u("cli/cp.py","cp",
  ("C9.S3",[126,129],"one resolve_existing_path call per source where a bulk resolver exists"))
u("cli/org.py","get_user_id",
  ("C1.S4",[36,38],"input lowercased twice"))
# bindings core
u("bindings/dxdatabase_functions.py","_download_dxdatabasefile",
  ("C1.S5",[179,182],"describe issued whose `dxdatabase_desc` is never read"),
  ("C1.S5",[233,243,254,261],"`verify_part` never called but every chunk is still md5-hashed and discarded"),
  ("C1.S7",[186,193,198,203],"one-element parts dict built, sorted and iterated"))
u("bindings/dxdatabase_functions.py","download_dxdatabasefile",
  ("C8.S4",[77,90],"each retry re-describes when describe_output not supplied"))
u("bindings/dxdatabase.py","DXDatabase.get_download_url",
  ("C3.S2",[176,179],"`object_exists_in_project` HTTP describe runs before the URL cache check, once per chunk"))
u("bindings/dxfile_functions.py","_download_dxfile",
  ("C1.S5",[428,440,494,497],"`md5_hasher()` and `update()` per chunk even when the part has no md5; digest discarded"),
  ("C3.S5",[458],"list.index over parts_to_get while resuming"))
u("bindings/dxfile_functions.py","download_dxfile",
  ("C8.S4",[131,143],"each retry re-enters _download_dxfile which re-describes"))
u("bindings/dxfile_functions.py","list_subfolders",
  ("C9.S2",[750],"describes the whole project folder list and filters client-side"),
  ("C3.S2",[754,756],"`path + '/'` and `path == '/'` recomputed per element"))
u("bindings/dxfile_functions.py","download_folder",
  ("C11.S5",[826,845],"files downloaded strictly one after another"),
  ("C8.S1",[827,845],"`compose_local_dir` recomputed per file; `remote_file['describe']` re-indexed per iteration"))
u("bindings/dxfile_functions.py","upload_local_file",
  ("C3.S2",[571,592,650,653],"`can_be_mmapd(fd)` fstat per part, `_get_creation_params(kwargs)` per retry"))
u("bindings/dxfile_functions.py","_verify_checksum",
  ("C1.S1",[231,237],"referenced only from tests; the download loop uses _IncrementalChecksum"))
u("bindings/dxfile_functions.py","_which",
  ("C10.S1",[],"hand-written PATH scan that `shutil.which` provides"))
u("bindings/dxfile.py","DXFile.write",
  ("C6.S2",[559,566],"`bytes(data)` copies an mmap or bytearray part (up to 96 MB) before upload"))
u("bindings/dxfile.py","DXFile._write2",
  ("C6.S2",[524,532],"recursion slices `data[remaining:]` per level, copying the tail repeatedly; quadratic for large writes"),
  ("C7.S3",[532],"recursion per buffer-sized chunk could be a loop"))
u("bindings/dxfile.py","DXFile.upload_part",
  ("C1.S3",[651,664],"`data` is asserted bytes so the buffer-like branch with rewind and 4 MB loop can never run"))
u("bindings/dxfile.py","DXFile.__iter__",
  ("C10.S4",[327,328],"`_buffer += more` then `split` on the entire buffer each read; quadratic when there are no newlines"))
u("bindings/dxfile.py","DXFile._read2",
  ("C6.S2",[923,933],"read data copied three times through BytesIO, `buf.read()` and tail slice"),
  ("C9.S2",[883],"full describe for size and state"))
u("bindings/__init__.py","DXDataObject._wait_until_parts_uploaded",
  ("C3.S1",[673],"`any(parts[key].get(...) for key in parts)` re-indexes per key"))
u("bindings/dxfile.py","DXFile.__init__",
  ("C1.S6",[227,228],"read and write buffers allocated eagerly for every handle"))
u("bindings/dxfile.py","_get_write_buf_size",
  ("C1.S2",[115],"`buffer_size_hint = buffer_size_hint` no-op"))
u("bindings/dxfile.py","_readable_part_size",
  ("C4.S2",[],"range chain re-tests lower bounds already excluded by the preceding branch"))
u("bindings/dxglobalworkflow.py","DXGlobalWorkflow.describe_underlying_workflow",
  ("C8.S1",[181,195],"per-region cache is read but never written; line 194 replaces the dict, so every call makes a describe"))
u("bindings/dxglobalworkflow.py","DXGlobalWorkflow.get_underlying_workflow",
  ("C8.S1",[215,227],"`_workflows_by_region` never populated; each call creates two DXWorkflow handlers"))
u("bindings/dxglobalworkflow.py","DXGlobalWorkflow._get_run_input",
  ("C8.S4",[262,264],"project_describe per run to get region with no memo"))
u("bindings/download_all_inputs.py","_gen_helper_dict",
  ("C8.S4",[88,89],"re-runs get_job_input_filenames (describe per file) already done by the caller"),
  ("C1.S3",[91,103],"`add_if_no_collision` can never collide"))
u("bindings/download_all_inputs.py","download_all_inputs",
  ("C5.S1",[172,179],"`d.split('/')[0] in exclude` list membership per directory"),
  ("C8.S4",[161,162],"inputs parsed and described twice"))
u("bindings/mount_all_inputs.py","_gen_helper_dict",
  ("C8.S4",[55,56],"same double parse and per-file describe as download_all_inputs"))
u("bindings/mount_all_inputs.py","mount_all_inputs",
  ("C10.S1",[125,152,153,161],"spawns mkdir, id -u, id -g and find subprocesses where os.mkdir/getuid/getgid do the same"))
u("bindings/search.py","_find",
  ("C3.S5",[97,108],"after the limit is reached on a page with a next token another API page is requested"),
  ("C3.S3",[89,95],"`format_result` redefined for each page"))
u("bindings/search.py","org_find_apps",
  ("C3.S5",[1002,1005],"limit used only as page size; generator keeps paging until server exhausted"))
u("bindings/dxworkflow.py","DXWorkflow._get_stage_id",
  ("C5.S2",[164,196],"linear scans of self.stages per call, once per input key"),
  ("C6.S3",[185],"`any([...])` builds a list and loses early exit; re.compile per call"))
u("bindings/dxworkflow.py","DXWorkflow.get_stage",
  ("C1.S4",[251,255],"resolves the id (scan) then scans stages again"))
u("bindings/dxjob.py","DXJob.wait_on_done",
  ("C1.S8",[322,340],"fixed 2 s polling for up to 7 days versus exponential backoff used elsewhere"))
u("bindings/dxanalysis.py","DXAnalysis.wait_on_done",
  ("C1.S8",[122,140],"fixed 2 s polling loop"))
u("bindings/__init__.py","verify_string_dxid",
  ("C8.S2",[44,45],"regex string built and joined per call, run on every set_ids"))
u("bindings/__init__.py","DXDataObject.set_ids",
  ("C4.S2",[286,299],"link validated twice; `elif project is not None` always true"))
u("bindings/dxdataobject_functions.py","describe",
  ("C1.S4",[207,215],"is_dxlink then re-index and get_dxlink_ids runs is_dxlink again"))
u("bindings/dxapplet.py","DXExecutable._get_run_input_common_fields",
  ("C1.S6",[61,66],"builds four SystemRequirementsDict even when one input is set; repeated kwargs.get"))
u("bindings/dxapp.py","DXApp.update",
  ("C1.S1",[249,252],"`resp =` never read"))
u("bindings/dxproject.py","DXContainer.describe",
  ("C4.S3",[],"`isinstance(self, DXProject)` per call to choose an API function"))
# top-level
u("__init__.py","DXHTTPRequest",
  ("C8.S2",[727],"every exception, including expected 4xx DXAPIError, clears the pool manager, dropping all keep-alive connections"),
  ("C3.S3",[597,600,616],"`ensure_ascii` closure redefined per retry; URL encoded to bytes only to be thrown away"))
u("__init__.py","_get_pool_manager",
  ("C8.S2",[246,284],"default_pool_args dict and env checks rebuilt per request; custom-cert path builds a new PoolManager per call"))
u("__init__.py","_get_env_var_proxy",
  ("C3.S5",[235,244],"loop keeps scanning after a variable is found and takes the last match; callers call it twice"))
u("__init__.py","_debug_print_request",
  ("C1.S4",[414,418],"re-runs `json.dumps(data)` although serialized_data already built"))
u("__init__.py","append_underlying_workflow_describe",
  ("C11.S5",[1035,1038],"workflow_describe per region, sequential"))
u("system_requirements.py","SystemRequirementsDict.__init__",
  ("C6.S2",[38],"always deep-copies its input, including for freshly built dicts"))
u("system_requirements.py","SystemRequirementsDict.override_cluster_spec",
  ("C7.S4",[145,148,151,168],"deep-copies all entrypoints then filters then constructor copies again"))
u("system_requirements.py","SystemRequirementsDict._add_dict_values",
  ("C10.S2",[196],"`set(list(d1.keys()) + list(d2.keys()))` builds two lists"))
u("system_requirements.py","SystemRequirementsDict.override_spec",
  ("C1.S2",[175,177],"`dict.fromkeys` filled then overwritten per key"))
u("app_builder.py","upload_resources",
  ("C7.S4",[316,405,413,427],"every file is read into a temp tar before the checksum/lookup that may discard it"),
  ("C10.S1",[441,455],"uncompressed tar re-read through a hand-written 8 KB loop into a second tar.gz"),
  ("C6.S3",[288],"`len(os.listdir(resources_dir)) > 0` materialises the listing"),
  ("C1.S4",[350,371],"`os.path.islink` re-lstat of an already stat-ed path"))
u("app_builder.py","upload_applet",
  ("C9.S3",[623,667],"up to three sequential describes per asset dependency, full describe for name"),
  ("C3.S2",[537,552],"folder setup and list_folder existence check per colliding applet"))
u("app_builder.py","_create_app",
  ("C1.S6",[900],"`app_list_authorized_users` called unconditionally"),
  ("C9.S1",[849,896],"three list calls before add/remove calls that one app_describe would answer"),
  ("C6.S7",[774,783],"`inherited_metadata={}` mutable default mutated via app_spec"))
u("app_builder.py","is_link_local",
  ("C3.S5",[208,215],"loop keeps doing abspath/join after is_local is False"))
u("app_builder.py","build",
  ("C1.S5",[156,168],"`os.path.abspath` evaluated inside debug `.format` eagerly"))
u("executable_builder.py","verify_developer_rights",
  ("C6.S1",[154],"namedtuple class built on every call"))
u("executable_builder.py","get_valid_bill_to",
  ("C1.S6",[108],"`dxpy.whoami()` API call made before the branches that need it"))
u("executable_builder.py","assert_consistent_reg_options",
  ("C3.S2",[207,228],"`set(...keys())` rebuilt several times per iteration; `json_spec.get('runSpec', {})` per key"))
u("workflow_builder.py","_assert_executable_regions_match",
  ("C8.S1",[387,413],"no memoisation across stages that share an executable; each does two describes"))
u("workflow_builder.py","_get_validated_json",
  ("C6.S2",[316],"spec deep-copied here and again in `_get_validated_json_for_build_or_update`"))
u("workflow_builder.py","_build_global_workflow",
  ("C6.S2",[563],"deep-copies the whole spec only to delete two keys"))
u("workflow_builder.py","_cleanup_empty_keys",
  ("C5.S4",[72,75],"json.dumps, regex, json.loads round trip to drop empty values"))
u("asset_builder.py","build_asset",
  ("C1.S5",[197],"`system_whoami()` result discarded"),
  ("C11.S5",[212,215],"three independent uploads run serially"),
  ("C9.S1",[274,288],"three single-object remove calls instead of one remove_objects"))
u("ssh_tunnel_app_support.py","poll_for_server_running",
  ("C9.S2",[49,55],"full job describe every 5 s to read tags and state"))
u("ssh_tunnel_app_support.py","get_notebook_app_versions",
  ("C9.S3",[84,85],"describe per app returned by find_apps"))
u("scripts/dx_build_app.py","build_and_upload_locally",
  ("C3.S2",[887,896,901,913],"multi-region apps re-walk, re-tar, re-hash the same src_dir and re-parse dxapp.json per region"),
  ("C8.S4",[793,843,846],"region of working_project described twice"),
  ("C1.S5",[975,984],"`app_describe` always runs though its result is needed only for logging or return_object_dump"))
u("scripts/dx_build_app.py","_check_suggestions",
  ("C9.S3",[99,155],"per-suggestion describe with no dedupe; results unused"))
u("scripts/dx_build_app.py","_check_file_syntax",
  ("C10.S2",[284,291],"each .py compiled to a .pyc on disk and unlinked; `compile()` avoids disk"),
  ("C6.S6",[324],"unclosed `open(filename)` test read"),
  ("C6.S1",[278,297],"nested checker functions redefined per call"))
u("scripts/dx_build_app.py","_lint",
  ("C8.S4",[171,225,232],"dxapp.json re-opened and re-parsed; `re.match` per field"))
u("scripts/dx_build_app.py","_build_app",
  ("C4.S1",[1048,1050],"`any([x for x in [a, b]])` and is_importer_job file read before the cheaper test"))
u("scripts/dx_build_app.py","_verify_app_source_dir_impl",
  ("C10.S2",[412,427,445],"`re.match('^(org-|user-)')` for startswith; `os.path.join` repeated per file"))
u("nextflow/collect_images.py","_populate_cached_file_ids",
  ("C8.S4",[401,428],"processes that share an image each issue their own find_data_objects, serially"))
u("nextflow/collect_images.py","_docker_manifest_inspect",
  ("C3.S5",[147,162],"retries three times over minutes even for permanent failures"))
u("nextflow/collect_images.py","bundle_docker_images",
  ("C11.S5",[60,70],"pull, save, upload per image strictly sequential"))
u("nextflow/ImageRef.py","ImageRef._dx_file_get_name",
  ("C9.S2",[80,82],"full describe for the name already fetched earlier and discarded"))
u("nextflow/ImageRefFactory.py","ImageRefFactory.__init__",
  ("C8.S2",[27,29],"`_imageRef_switch` dict rebuilt per instance"))
u("nextflow/nextflow_builder.py","build_pipeline_with_npi",
  ("C8.S4",[104,119],"DXApp handle created and described twice"),
  ("C1.S5",[104],"`resolve_version` result dropped"))
u("nextflow/nextflow_builder.py","prepare_nextflow",
  ("C6.S3",[159],"`glob(...)` full list only to test for emptiness"))
u("nextflow/nextflow_builder.py","prepare_custom_inputs",
  ("C5.S1",[192,213,232,241,242],"`property_key in required_inputs` list scan, `inputs.insert(0, ...)` O(n) per input, dict literals rebuilt per property"))
u("nextflow/nextflow_templates.py","get_nextflow_src",
  ("C10.S4",[85,97],"`applet_runtime_params = applet_runtime_params + ...` and `exclude_input_download +=` in a loop over inputs"))
u("nextflow/nextflow_utils.py","_load_versions_manifest",
  ("C8.S1",[14,37],"JSON opened, parsed and schema-checked on every call, at least twice per build"))
u("nextflow/nextflow_utils.py","find_readme",
  ("C4.S1",[137,141],"stats every entry before the cheap regex; builds two lists and sorts to take the minimum"))
u("nextflow/nextflow_utils.py","get_project_with_assets",
  ("C9.S1",[100],"describe API round trip only as an existence check on every build"))
u("nextflow/validate_nextflow_assets.py","validate_assets",
  ("C8.S1",[91,110],"files loaded and regex-validated once per reference"))
u("templating/utils.py","create_files_from_templates",
  ("C3.S1",[315,321],"seven chained `.replace` calls rescan the text"),
  ("C10.S2",[290],"`any(generator of endswith)` can be `endswith(tuple)`"))
u("templating/python.py","get_strings",
  ("C1.S2",[73,77],"initial `''` assignments overwritten before use"),
  ("C10.S4",[109,120],"`dl_files_str +=` repeated up to four times"))
u("templating/python.py","get_output_fmt",
  ("C1.S2",[38],"`output_fmt = ''` overwritten before use"))
# dx.py
D="scripts/dx.py"
u(D,"rm",
  ("C8.S4",[895,914,916,919],"with -r and no --force every path is resolved once in the safety-check loop and again in the main loop"),
  ("C4.S7",[962,970],"`project_remove_objects` called for every project even when its objects list is empty"))
u(D,"upload_one",
  ("C3.S2",[2136,2171],"per file: `try_call(process_dataobject_args, args)`, `resolve_path` on the same folder string, and `copy.copy(args)`"))
u(D,"find_executions",
  ("C9.S2",[2249,2265,2354,2380],"first-pass query in trees mode asks for the full describe_args though only originJob/rootExecution/try are read"),
  ("C5.S1",[2433,2434,2445,2447],"`executions_by_parent[parent]` is a list and `not in` scans it per result"),
  ("C6.S3",[2454],"`len(list(roots.keys())) > 0` builds a list to test emptiness"))
u(D,"get_database",
  ("C1.S5",[1947,1948,1950,1975],"debug messages formatted eagerly (including the whole folder listing) while logging is at INFO"),
  ("C11.S5",[1977,1990],"database files downloaded one at a time"))
u(D,"run_body",
  ("C6.S2",[3234],"`copy.deepcopy(args.cloned_job_desc)` to read one key"),
  ("C9.S3",[3387,3390],"`dxpy.describe(stage_desc['executable'])` per stage, no dedupe"),
  ("C1.S4",[3414,3424],"parentAnalysis condition evaluated in a comprehension and again in a loop"))
u(D,"cd",
  ("C1.S6",[737,743],"full project describe unconditionally though the name is only used on one branch"))
u(D,"describe",
  ("C4.S7",[1336,1344],"find_apps and find_global_workflows still called after a data-object match with no colon"))
u(D,"ssh",
  ("C6.S6",[4122,4148],"proxy socket and file created per retry and only the last pair closed; non-proxy socket never closed"),
  ("C1.S8",[4079,4086,4093,4101],"fixed `sleep(1)` describe polling"),
  ("C1.S4",[4069,4073],"`all(ip in job_allow_ssh ...)` followed by a second loop doing the same tests"))
u(D,"generate_batch_inputs",
  ("C3.S3",[4208,4224],"`flatten_batch` redefined per batch iteration; `headers` recomputed from loop-invariant `input_names`; `sorted(...items())` twice per row"))
u(D,"tree",
  ("C3.S2",[1118,1119,1126,1137],"startswith prefix rebuilt per folder; `BOLD() + BLUE() + path_element + ENDC()` rebuilt for every path element"))
u(D,"get_output_path",
  ("C6.S3",[1891],"`len(os.listdir(output_path))` lists the whole directory to test emptiness"))
u(D,"wait",
  ("C6.S6",[2715],"`open(args.path[0]).read()` never closed"))
u(D,"print_run_help",
  ("C10.S4",[3474,3506,3560],"`exec_help += ...` in nested loops"),
  ("C5.S1",[3506,3560],"`param['name'] in advanced_inputs` list search per parameter"))
u(D,"DXCLICompleter.get_matches",
  ("C9.S2",[286,299],"lists all apps on first tab for run/install/uninstall then filters client-side twice"))
u(D,"find_apps_result",
  ("C9.S2",[2586,2589],"`--installed` filtered client-side after pulling every app"))
u(D,"ls",
  ("C8.S4",[796],"full project describe only to print the name in verbose mode"))
u(D,"archive",
  ("C6.S2",[4416,4417],"`copy.deepcopy(request_input)` only to add dryRun"),
  ("C9.S1",[4374,4397],"`find_data_objects` once per non-ID file path"))

def add(path, qn, rc, lines, why):
    name=P+path+"::"+qn
    for r in U:
        if r["unit"]==name:
            r["suspicions"].append({"label":"abcdefghij"[len(r["suspicions"])],"root_cause":rc,"lines":lines,"why":why}); return
    u(path,qn,(rc,lines,why))
add("utils/pretty_print.py","flatten_json_array","C3.S2",[206],"the replacement string `'\"{}\": [\\1 '.format(array_name)` is rebuilt on every pass of the while loop")
add("scripts/dx.py","find_executions","C7.S4",[2386],"sorts the whole executions_cache with a key lambda and then slices [:args.num_results]")
add("__init__.py","DXHTTPRequest","C3.S2",[686,771],"`range_str` built from `headers` inside the retry loop although headers do not change")
add("dx_extract_utils/germline_utils.py","filter_results","C5.S1",[329],"`entry[key] not in restricted_values` scans a list for every result entry")
add("dx_extract_utils/germline_utils.py","get_types_to_filter_out_when_infering","C5.S1",[56,57],"constant list literal rebuilt per call and `type not in requested_types` list scan")
add("dx_extract_utils/germline_utils.py","get_germline_ref_payload","C3.S1",[160,165],"append-only loop builds `allele_filters` that a comprehension would build")
add("utils/describe.py","print_app_desc","C5.S1",[549,550,609],"`recognized_fields` list rebuilt per call and searched linearly per key")
add("utils/describe.py","print_globalworkflow_desc","C5.S1",[614,617,677],"`recognized_fields` list rebuilt per call and searched linearly per key")
add("utils/describe.py","print_execution_desc","C5.S1",[812,825,1002],"`recognized_fields` list rebuilt per call and searched linearly per key")
add("utils/pretty_print.py","format_timedelta","C10.S4",[245],"`out_str = str(val) + ... + out_str` prepends in a loop")
add("utils/describe.py","io_val_to_str","C1.S4",[229,231,233],"`val['$dnanexus_link']` re-indexed up to five times per value")
add("utils/pretty_print.py","format_tree","C3.S1",[97,98],"index-based iteration over `nodes` with repeated `tree[node]` lookups and `len(nodes)-1` recomputed per node")
add("utils/local_exec_utils.py","get_implicit_depends_on","C3.S1",[165,193],"index-based iteration with repeated re-indexing of the element")
add("utils/resolver.py","resolve_global_executable","C4.S1",[1245,1246],"`is_hashid(path)` regex run before the cheap `is_version_required` flag test")
add("workflow_builder.py","_validate_json_for_global_workflow","C6.S3",[300],"`all([isinstance(...) for ...])` builds a list and loses early exit")
add("__init__.py","_is_retryable_exception","C1.S3",[331,333],"if-return-True/return-False over a boolean test")
add("cli/dataset_utilities.py","DXDatasetDictionary.get_join_path_to_entity_field_map","C8.S3",[2152,2189],"`entity[\"fields\"][field][\"mapping\"]` and `entity[\"name\"]` re-resolved per field; iterates keys then indexes")
add("cli/dataset_utilities.py","DXDatasetDictionary.load_coding_dictionary","C8.S3",[2208,2230],"`descriptor.model[\"entities\"]` re-resolved through the outer key per entity")
add("cli/dataset_utilities.py","list_fields","C3.S2",[1144,1168],"per-field loop with append-only accumulation and sorted() on keys")
add("cli/dataset_utilities.py","has_access_level","C5.S3",[1810],"constant `level_rank` list built per call and `.index` twice")
add("scripts/dx_build_app.py","build_app_from","C3.S2",[699,755],"loop-invariant expression inside the loop (scan rule)")

with open("/home/javad/energy-run/dx-toolkit/step1.jsonl","w") as f:
    for r in U: f.write(json.dumps(r)+"\n")
print(len(U))
