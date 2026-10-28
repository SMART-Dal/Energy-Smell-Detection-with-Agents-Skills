# Energy report — dx-toolkit @ accd86a

211 units listed, 94 with an accepted suspicion · 13 repairs submitted, 100 deferred · 5 confirmed · 5 partial · 2 negligible · 1 no_inputs · 5 applied
Noise floor 1.2% (from: session calibration).

## Applied

### `src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON` — C1S1-validate-json-dead-read (C1.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +100.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| case-4-allele | 109.88 | 0.05 | +100.0% | 0.0% | yes |
| case-5-variant | 109.57 | 0.01 | +100.0% | 0.0% | yes |
| case-6-allele | 108.96 | 0.02 | +100.0% | 0.0% | yes |
| case-7-variant | 103.45 | 0.04 | +100.0% | 0.0% | yes |

### `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` — C6S2-get-first-rfind (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +53.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colons-dense | 111.23 | 40.84 | +63.3% | 0.8% | yes |
| all-escaped-stars | 110.99 | 54.83 | +50.6% | 1.5% | yes |
| mixed-escapes | 110.12 | 55.22 | +49.9% | 1.1% | yes |
| mostly-escaped | 110.95 | 54.68 | +50.7% | 1.4% | yes |

### `src/python/dxpy/utils/resolver.py::get_last_pos_of_char` — C6S2-get-last-rfind (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +58.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-escaped-slashes | 100.03 | 53.43 | +46.6% | 0.9% | yes |
| gapped-escaped | 111.66 | 17.68 | +84.2% | 0.6% | yes |
| gapped-random-escaped | 106.99 | 30.74 | +71.3% | 0.1% | yes |
| escaped-colons | 79.47 | 53.60 | +32.6% | 0.8% | yes |

### `src/python/dxpy/dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter` — C6S2-pheno-comprehension (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +60.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| in-large-values | 100.61 | 41.21 | +59.0% | 2.5% | yes |
| not-in-large-values | 63.33 | 51.77 | +18.3% | 0.9% | yes |
| exists-plus-in | 102.50 | 16.59 | +83.8% | 0.1% | yes |
| multi-compound-match-later | 102.52 | 20.37 | +80.1% | 1.3% | yes |

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — C7S1-truncate-bsearch (C7.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| control-20k | 103.30 | 0.15 | +99.9% | 0.0% | yes |
| two-byte-20k | 102.36 | 0.30 | +99.7% | 0.0% | yes |
| four-byte-20k | 97.51 | 0.38 | +99.6% | 0.0% | yes |
| mixed-30k | 94.84 | 0.42 | +99.6% | 0.0% | yes |

## Measured, not confirmed

### `src/python/dxpy/utils/spelling_corrector.py::correct` — C1S4-correct-edits-once (C1.S4)

**partial** — saves energy on 2 of 4 inputs ('no-hit-len11', 'no-hit-len13'; best 2.9% +-1.1% on 'no-hit-len13'), and no saving that can be told from noise on the rest: 'edit2-hit-len12' +1.6% +-6.0% (its pairs disagree too much to tell); 'edit2-hit-len13' +3.1% +-3.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.5%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| edit2-hit-len12 | 62.44 | 61.45 | +1.6% | 6.0% | no: pairs disagree |
| edit2-hit-len13 | 54.64 | 52.94 | +3.1% | 3.8% | no: pairs disagree |
| no-hit-len11 | 57.21 | 55.77 | +2.5% | 0.3% | yes |
| no-hit-len13 | 60.91 | 59.15 | +2.9% | 1.1% | yes |

### `src/python/dxpy/utils/pathmatch.py::filter` — C3S1-pathmatch-comprehension (C3.S1)

**partial** — saves energy on 3 of 4 inputs ('low-hit-100k', 'deep-paths-80k', 'suffix-mix-100k'; best 10.5% +-7.4% on 'low-hit-100k'), and no saving that can be told from noise on the rest: 'exact-literal-120k' -1.7% +-2.6% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| low-hit-100k | 63.16 | 56.48 | +10.6% | 7.4% | yes |
| deep-paths-80k | 62.11 | 57.96 | +6.7% | 1.5% | yes |
| suffix-mix-100k | 55.52 | 54.25 | +2.3% | 1.0% | yes |
| exact-literal-120k | 53.88 | 54.79 | -1.7% | 2.6% | no: pairs disagree |

### `src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink` — C4S6-dlink-precheck (C4.S6)

**partial** — saves energy on 1 of 4 inputs ('big-array-no-link'; best 100.0% +-0.0% on 'big-array-no-link'), and no saving that can be told from noise on the rest: 'big-dict-no-link' +0.1% +-2.3% (its pairs disagree too much to tell); 'link-dict-pid' +0.5% +-0.6% (its pairs disagree too much to tell); 'link-dict-partial' +0.8% +-2.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +25.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-dict-no-link | 56.23 | 56.19 | +0.1% | 2.3% | no: pairs disagree |
| big-array-no-link | 108.34 | 0.01 | +100.0% | 0.0% | yes |
| link-dict-pid | 55.80 | 55.49 | +0.5% | 0.6% | no: pairs disagree |
| link-dict-partial | 55.89 | 55.45 | +0.8% | 2.7% | no: pairs disagree |

### `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec` — C6S2-cluster-copy-kept (C6.S2)

**partial** — saves energy on 1 of 4 inputs ('many-entrypoints-no-clusterspec'; best 99.8% +-0.0% on 'many-entrypoints-no-clusterspec'), and no saving that can be told from noise on the rest: 'wildcard-large-appdoc' -0.5% +-2.5% (its pairs disagree too much to tell); 'fallback-to-app-wildcard' +0.8% +-1.6% (its pairs disagree too much to tell); 'field-heavy-clusterspec' -0.7% +-0.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +24.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wildcard-large-appdoc | 56.89 | 57.18 | -0.5% | 2.5% | no: pairs disagree |
| fallback-to-app-wildcard | 63.65 | 63.16 | +0.8% | 1.6% | no: pairs disagree |
| many-entrypoints-no-clusterspec | 108.50 | 0.17 | +99.8% | 0.1% | yes |
| field-heavy-clusterspec | 56.37 | 56.74 | -0.7% | 0.8% | no: pairs disagree |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type` — C8S3-infer-hoist (C8.S3)

**partial** — saves energy on 3 of 4 inputs ('no-results', 'mixed-medium', 'many-loci-tiny-samples'; best 7.6% +-1.8% on 'no-results'), and no saving that can be told from noise on the rest: 'many-loci-few-samples' +6.2% +-7.1% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +5.7%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-loci-few-samples | 76.26 | 71.52 | +6.2% | 7.1% | no: pairs disagree |
| no-results | 64.89 | 59.97 | +7.6% | 1.8% | yes |
| mixed-medium | 67.61 | 63.65 | +5.9% | 1.6% | yes |
| many-loci-tiny-samples | 65.29 | 63.13 | +3.3% | 2.2% | yes |

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — C5S2-display-index (C5.S2)

**negligible** — no case moved more than the noise: the largest reading was +1.4% +-2.6% on 'hier-wide', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.4%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 80.01 | 80.42 | -0.5% | 1.2% | no: pairs disagree |
| hier-wide | 84.07 | 82.89 | +1.4% | 2.6% | no: pairs disagree |
| hier-paginated | 79.79 | 79.05 | +0.9% | 2.0% | no: pairs disagree |
| hier-no-concepts | 79.83 | 80.10 | -0.3% | 1.4% | no: pairs disagree |

### `src/python/dxpy/utils/config.py::DXConfig.get_session_conf_dir` — C1S6-sessions-guard (C1.S6)

**negligible** — no case moved more than the noise: the largest reading was +5.6% +-22.4% on 'cleanup-500-dead', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +3.0%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| cleanup-500-dead | 7.20 | 6.76 | +6.1% | 22.4% | no: pairs disagree |
| cleanup-mixed-names | 7.16 | 6.85 | +4.3% | 20.8% | no: pairs disagree |
| cleanup-alive-plus-dead | 3.72 | 3.59 | +3.7% | 26.4% | no: pairs disagree |
| cleanup-deep-trees | 7.02 | 7.18 | -2.2% | 6.0% | no: pairs disagree |

## Not measured

### `src/python/dxpy/cli/output_handling.py::write_expression_output` — C3S2-output-colset (C3.S2)

**no_inputs** — no inputs could be generated for src/python/dxpy/cli/output_handling.py::write_expression_output: the generator failed: BrokenPipeError: [Errno 32] Broken pipe. Next: the unit has had its 3 tries; its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.describe_underlying_workflow` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/search.py::_find` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/search.py::_find` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/search.py::_org_find` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/search.py::_org_find` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/mount_all_inputs.py::_gen_helper_dict` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/download_all_inputs.py::_gen_helper_dict` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/mount_all_inputs.py::mount_all_inputs` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::DXCLICompleter.get_matches` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::cd` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::rm` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::describe` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::describe` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::run_body` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::run_body` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::run_body` c: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::ssh` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::archive` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` a: deferred — the hoists are not written; they are small per-batch costs and were not measured in the time available
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` b: deferred — the hoists are not written; they are small per-batch costs and were not measured in the time available
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` c: deferred — the hoists are not written; they are small per-batch costs and were not measured in the time available
- `src/python/dxpy/utils/describe.py::get_resolved_jbors` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::resolve_multiple_existing_paths` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::resolve_job_ref` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::resolve_container_id_or_name` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::object_exists_in_project` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::resolve_path` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::resolve_path` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/resolver.py::split_unescaped` a: deferred — its repair needs get_last_pos_of_char to take an end bound, which would change a second unit's signature; not written
- `src/python/dxpy/utils/resolver.py::parse_input_keyval` a: deferred — the obvious repair (slice to the first '=') changes the result for a leading '=' (split_unescaped discards empty pieces); no exact repair written
- `src/python/dxpy/utils/describe.py::render_bundleddepends` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/collect_images.py::_populate_cached_file_ids` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/collect_images.py::_populate_cached_file_ids` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/collect_images.py::collect_docker_images` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/collect_images.py::collect_docker_images` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/ImageRef.py::ImageRef._package_bundle` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/nextflow/nextflow_builder.py::prepare_nextflow` a: deferred — removing the template copy is not written; it touches the filesystem and was not measured
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: blocked — inputs.py: it cannot run here: validate_cohort_ids unconditionally calls raw_api_call, a live HTTP POST to the Vizserver; no input avoids it and mocking the request is not allowed
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` b: deferred — the second suspicion (display_order computed then dropped when paginated) is a different edit to the same lines; not written
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: deferred — the assign result is unused; deleting that statement was not written and measured in the time available
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxdatabase.py::DXDatabase.get_download_url` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile_functions.py::_download_dxfile` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile_functions.py::upload_local_file` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile.py::DXFile._write2` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile.py::DXFile.write` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile.py::DXFile.__iter__` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile.py::DXFile.read` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/dxfile.py::DXFile._read2` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/pretty_print.py::format_table` a: deferred — table[0] is not equivalent: callers pass dict_values, which is not indexable, and next(iter()) changes the exception on an empty table; not submitted
- `src/python/dxpy/utils/pretty_print.py::format_table` b: deferred — table[0] is not equivalent: callers pass dict_values, which is not indexable, and next(iter()) changes the exception on an empty table; not submitted
- `src/python/dxpy/utils/completer.py::path_completer` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/file_load_utils.py::get_input_spec_patterns` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/local_exec_utils.py::get_nonclosed_data_obj_link` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/job_log_client.py::metrics_top` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/exec_utils.py::run` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/executable_unbuilder.py::_dump_app_or_applet` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/utils/pretty_print.py::flatten_json_array` a: deferred — a single-pass equivalent of the repeated substitution was not proven, so no repair was written
- `src/python/dxpy/__init__.py::_get_pool_manager` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/__init__.py::DXHTTPRequest` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/__init__.py::append_underlying_workflow_describe` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/app_builder.py::upload_resources` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/app_builder.py::upload_resources` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/app_builder.py::_create_app` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/app_builder.py::create_app_multi_region` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_get_validated_enabled_regions` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_create_temporary_projects` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_build_underlying_workflows` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/workflow_builder.py::_cleanup_empty_keys` a: deferred — replacing the regex round-trip with a dict pass needs the regex's exact semantics reproduced; not written
- `src/python/dxpy/executable_builder.py::get_permitted_regions` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/executable_builder.py::verify_developer_rights` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/ssh_tunnel_app_support.py::get_notebook_app_versions` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/ssh_tunnel_app_support.py::poll_for_server_running` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.descriptor_file_dict` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_info_dict` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_names_list` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_index` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/dx_extract_utils/retrieve_bins.py::retrieve_bins` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — inputs.py: the generator failed on all three tries with BrokenPipeError: [Errno 32] Broken pipe; the repair (one set per check instead of one per row) was written but could not be measured, so the line was moved out of submissions.jsonl
- `src/python/dxpy/scripts/dx_build_app.py::_check_file_syntax` a: deferred — in-memory compile instead of py_compile is not written; the suspicion is local but the repair was not measured in the time available
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx_build_app.py::build_and_upload_locally` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx_build_app.py::build_and_upload_locally` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx_build_app.py::build_app_from` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/scripts/dx_build_app.py::_build_app` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/workflow.py::add_stage` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/workflow.py::update_stage` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/workflow.py::update_workflow` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/cp.py::cp` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/download.py::download` a: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
- `src/python/dxpy/cli/download.py::download` b: deferred — needs the live platform (API calls, file or job downloads) that this session cannot reach, so the repair was not measured here
