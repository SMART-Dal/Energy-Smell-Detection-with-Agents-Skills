# Energy report — dx-toolkit @ accd86a

57 units listed, 46 with an accepted suspicion · 24 repairs submitted, 18 deferred · 10 confirmed · 3 partial · 5 regressed · 2 negligible · 4 over_limit · 10 applied
Noise floor 1.6% (from: session calibration).

## Applied

### `src/python/dxpy/utils/pretty_print.py::flatten_json_array` — pp-flatten

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +89.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| strings-300 | 113.36 | 15.47 | +86.4% | 0.3% | yes |
| strings-400 | 109.27 | 12.50 | +88.6% | 0.0% | yes |
| crlf-300 | 113.42 | 15.58 | +86.3% | 0.0% | yes |
| deep-inputspec | 111.53 | 3.60 | +96.8% | 0.0% | yes |

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — dxlog-bsearch

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| control-20k | 104.10 | 0.16 | +99.8% | 0.0% | yes |
| two-byte-20k | 105.59 | 0.30 | +99.7% | 0.0% | yes |
| four-byte-20k | 98.84 | 0.38 | +99.6% | 0.0% | yes |
| mixed-30k | 98.25 | 0.44 | +99.6% | 0.0% | yes |

### `src/python/dxpy/dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter` — cohort-pheno-reduce

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +60.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| in-large-values | 116.20 | 48.12 | +58.6% | 0.7% | yes |
| not-in-large-values | 72.72 | 58.93 | +19.0% | 0.4% | yes |
| exists-plus-in | 115.57 | 18.66 | +83.9% | 0.0% | yes |
| multi-compound-match-later | 115.10 | 23.18 | +79.9% | 0.3% | yes |

### `src/python/dxpy/utils/resolver.py::split_unescaped` — resolver-split

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +67.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colon-escaped | 116.79 | 29.61 | +74.6% | 0.9% | yes |
| spaces-escaped | 117.04 | 29.68 | +74.6% | 1.4% | yes |
| backslash-runs | 103.17 | 57.75 | +44.0% | 0.4% | yes |
| mixed-include-empty | 116.76 | 25.21 | +78.4% | 0.4% | yes |

### `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` — resolver-first-pos

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +87.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colons-dense | 118.74 | 0.01 | +100.0% | 0.0% | yes |
| all-escaped-stars | 115.71 | 57.06 | +50.7% | 1.7% | yes |
| mixed-escapes | 117.68 | 0.05 | +100.0% | 0.0% | yes |
| mostly-escaped | 117.54 | 0.02 | +100.0% | 0.1% | yes |

### `src/python/dxpy/utils/resolver.py::get_last_pos_of_char` — resolver-last-pos

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +56.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-escaped-slashes | 107.04 | 57.87 | +45.9% | 0.6% | yes |
| gapped-escaped | 116.64 | 21.67 | +81.4% | 0.1% | yes |
| gapped-random-escaped | 118.30 | 36.34 | +69.3% | 0.5% | yes |
| escaped-colons | 78.47 | 54.85 | +30.1% | 2.5% | yes |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type` — gu-infer-hoist

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +10.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-loci-few-samples | 78.55 | 70.31 | +10.5% | 7.4% | yes |
| no-results | 72.69 | 64.06 | +11.9% | 2.0% | yes |
| mixed-medium | 73.46 | 65.36 | +11.0% | 1.2% | yes |
| many-loci-tiny-samples | 69.95 | 65.39 | +6.5% | 2.6% | yes |

### `src/python/dxpy/nextflow/nextflow_templates.py::get_nextflow_src` — nt-concat

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +7.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| files-200 | 62.72 | 57.49 | +8.3% | 2.7% | yes |
| strings-300-abs-resources | 62.60 | 57.43 | +8.3% | 0.7% | yes |
| mixed-150-file-heavy | 60.57 | 56.76 | +6.3% | 0.8% | yes |
| mixed-400-profile-resources | 63.97 | 59.85 | +6.4% | 1.8% | yes |

### `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` — nb-insert

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +19.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-required | 95.02 | 60.71 | +36.1% | 1.3% | yes |
| union-types | 70.97 | 61.44 | +13.4% | 1.4% | yes |
| path-formats | 71.46 | 60.60 | +15.2% | 1.3% | yes |
| many-definitions | 70.08 | 59.92 | +14.5% | 1.2% | yes |

### `src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON` — fp-validate

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +100.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| case-4-allele | 144.69 | 0.07 | +100.0% | 0.0% | yes |
| case-5-variant | 140.99 | 0.01 | +100.0% | 0.0% | yes |
| case-6-allele | 141.70 | 0.01 | +100.0% | 0.0% | yes |
| case-7-variant | 150.15 | 0.03 | +100.0% | 0.0% | yes |

## Measured, not confirmed

### `src/python/dxpy/utils/spelling_corrector.py::_known_edits2` — spell-edits2

**regressed** — the repair costs more than the code it replaces: 15474.1% lost on 'len8-sparse', above the 1.6% noise floor, and no case improved. Worse on 4 of 4 cases ('len7-mid-hit', 'len8-sparse', 'len9-sparse', 'len8-repeats').
Mean saving across its cases: -11191.7%.
Also the repair for suspicion(s) a of this unit.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| len7-mid-hit | 4.55 | 591.71 | -12909.7% | 1587.7% | yes |
| len8-sparse | 5.00 | 778.32 | -15469.5% | 1550.0% | yes |
| len9-sparse | 6.12 | 302.24 | -4840.8% | 244.1% | yes |
| len8-repeats | 6.09 | 709.38 | -11546.7% | 1016.9% | yes |

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — dd-coding-index

**negligible** — no case moved more than the noise: the largest reading was -0.6% +-2.7% on 'hier-paginated', against a clean 1.6% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 73.88 | 73.83 | +0.1% | 3.8% | no: pairs disagree |
| hier-wide | 77.71 | 77.45 | +0.3% | 2.8% | no: pairs disagree |
| hier-paginated | 74.35 | 74.81 | -0.6% | 2.7% | no: pairs disagree |
| hier-no-concepts | 71.49 | 71.25 | +0.3% | 3.3% | no: pairs disagree |

### `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec` — sr-cluster-copy

**partial** — saves energy on 1 of 4 inputs ('many-entrypoints-no-clusterspec'; best 99.8% +-0.0% on 'many-entrypoints-no-clusterspec'), and no saving that can be told from noise on the rest: 'wildcard-large-appdoc' +0.8% +-2.6% (its pairs disagree too much to tell); 'fallback-to-app-wildcard' +0.4% +-1.2% (its pairs disagree too much to tell); 'field-heavy-clusterspec' -0.1% +-1.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +25.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wildcard-large-appdoc | 65.36 | 64.84 | +0.8% | 2.6% | no: pairs disagree |
| fallback-to-app-wildcard | 72.57 | 72.27 | +0.4% | 1.2% | no: pairs disagree |
| many-entrypoints-no-clusterspec | 106.33 | 0.17 | +99.8% | 0.0% | yes |
| field-heavy-clusterspec | 54.44 | 54.48 | -0.1% | 1.4% | no: pairs disagree |

### `src/python/dxpy/bindings/search.py::_find` — search-limit

**regressed** — the repair costs more than the code it replaces: 22.4% lost on 'big-pages', above the 1.6% noise floor, and no case improved. Worse on 4 of 4 cases ('large-pages', 'capped-limit', 'kwarg-project', 'big-pages').
Mean saving across its cases: -21.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-pages | 55.36 | 67.15 | -21.3% | 5.3% | yes |
| capped-limit | 55.21 | 66.21 | -19.9% | 4.3% | yes |
| kwarg-project | 55.08 | 67.97 | -23.4% | 3.1% | yes |
| big-pages | 55.15 | 67.48 | -22.4% | 2.0% | yes |

### `src/python/dxpy/utils/pretty_print.py::escape_unicode_string` — pp-escape

**negligible** — no case moved more than the noise: the largest reading was -0.6% +-3.0% on 'all-controls', against a clean 1.6% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-controls | 81.02 | 81.48 | -0.6% | 3.0% | no: pairs disagree |
| backslash-heavy | 77.02 | 76.77 | +0.3% | 1.6% | no: pairs disagree |
| mixed-random | 79.32 | 79.65 | -0.4% | 2.0% | no: pairs disagree |
| tabs-and-cr | 77.19 | 77.21 | -0.0% | 1.3% | no: pairs disagree |

### `src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink` — resolver-dxlink

**partial** — saves energy on 1 of 4 inputs ('big-array-no-link'; best 100.0% +-0.0% on 'big-array-no-link'), and no saving that can be told from noise on the rest: 'big-dict-no-link' +0.3% +-2.3% (its pairs disagree too much to tell); 'link-dict-pid' +0.2% +-1.4% (its pairs disagree too much to tell); 'link-dict-partial' +0.3% +-1.5% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +25.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-dict-no-link | 72.66 | 72.45 | +0.3% | 2.3% | no: pairs disagree |
| big-array-no-link | 139.58 | 0.01 | +100.0% | 0.0% | yes |
| link-dict-pid | 71.73 | 71.59 | +0.2% | 1.4% | no: pairs disagree |
| link-dict-partial | 71.67 | 71.46 | +0.3% | 1.5% | no: pairs disagree |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_results` — gu-harmonize-results

**regressed** — the repair costs more than the code it replaces: 14.3% lost on 'large', above the 1.6% noise floor, and no case improved. Worse on 4 of 4 cases ('wide-fields', 'many-results', 'dense', 'large').
Mean saving across its cases: -10.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-fields | 72.44 | 79.79 | -10.1% | 1.1% | yes |
| many-results | 72.00 | 81.75 | -13.5% | 12.5% | yes |
| dense | 72.42 | 75.51 | -4.3% | 3.6% | yes |
| large | 71.78 | 82.02 | -14.3% | 3.0% | yes |

### `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` — nb-required-set

**partial** — saves energy on 3 of 4 inputs ('all-required', 'union-types', 'path-formats'; best 6.9% +-2.3% on 'all-required'), and no saving that can be told from noise on the rest: 'many-definitions' -1.8% +-2.3% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.2%.
The agent measured `mixed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-required | 84.20 | 78.39 | +6.9% | 2.3% | yes |
| union-types | 79.07 | 76.04 | +3.8% | 1.4% | yes |
| path-formats | 77.38 | 74.40 | +3.8% | 1.9% | yes |
| many-definitions | 73.37 | 74.69 | -1.8% | 2.3% | no: pairs disagree |

### `src/python/dxpy/utils/pretty_print.py::format_table` — pp-table-len

**regressed** — the repair costs more than the code it replaces: 1.6% lost on 'many-duplicates', above the 1.6% noise floor, and no case improved. Worse on 2 of 4 cases ('narrow-truncation', 'many-duplicates').
Mean saving across its cases: -1.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-12col | 76.65 | 77.80 | -1.5% | 2.6% | no: pairs disagree |
| narrow-truncation | 72.76 | 74.08 | -1.8% | 1.3% | yes |
| no-column-names | 72.94 | 74.22 | -1.8% | 1.9% | no: pairs disagree |
| many-duplicates | 76.12 | 77.34 | -1.6% | 1.1% | yes |

### `src/python/dxpy/utils/describe.py::format_currency` — describe-locale

**regressed** — the repair costs more than the code it replaces: 35.3% lost on 'huge-value', above the 1.6% noise floor, and no case improved. Worse on 4 of 4 cases ('en-gb-large', 'zero-usage', 'explicit-locale', 'huge-value').
Mean saving across its cases: -39.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| en-gb-large | 60.22 | 84.03 | -39.5% | 7.5% | yes |
| zero-usage | 58.39 | 82.66 | -41.6% | 9.0% | yes |
| explicit-locale | 57.49 | 81.41 | -41.6% | 3.7% | yes |
| huge-value | 62.06 | 83.94 | -35.2% | 3.2% | yes |

## Not measured

### `src/python/dxpy/cli/output_handling.py::write_expression_output` — oh-sets

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` — dd-load-assign

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — dxlog-encode

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `src/python/dxpy/utils/resolver.py::resolve_path` — resolver-colon

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/utils/resolver.py::resolve_path` a: deferred — over_limit: 20 repairs already had a verdict, so verify.py did not measure it
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: blocked — inputs.py: it cannot run here: `validate_cohort_ids` unconditionally calls `raw_api_call`, which performs a network POST to the Vizserver via `dxpy.DXHTTPRequest`; there is no input that avoids this server request, and `err_exit` would termi
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` b: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: blocked — verify.py: no_inputs; inputs.py: only 0 of 8 generated inputs ran and repeated on the original code (most often: the original raises KeyError: 'coding_name')
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: blocked — inputs.py: it cannot run here: `extract_assay_expression` only reaches its real work after `resolve_existing_path(args.path)` and `DXRecord(...)` / `Dataset.resolve_cohort_to_dataset(...)`, which require authenticated network access to the D
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: blocked — inputs.py: it cannot run here: `extract_assay_expression` only reaches its real work after `resolve_existing_path(args.path)` and `DXRecord(...)` / `Dataset.resolve_cohort_to_dataset(...)`, which require authenticated network access to the D
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` c: blocked — inputs.py: it cannot run here: `extract_assay_expression` only reaches its real work after `resolve_existing_path(args.path)` and `DXRecord(...)` / `Dataset.resolve_cohort_to_dataset(...)`, which require authenticated network access to the D
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_germline` a: blocked — inputs.py: it cannot run here: `extract_assay_germline` requires DNAnexus platform access — it calls `dxpy.DXHTTPRequest` (via `resolve_validate_record_path`, `raw_api_call`, `raw_query_api_call`) and `DXDataset(...).get_descriptor()` to fet
- `src/python/dxpy/cli/dataset_utilities.py::get_codings` a: blocked — inputs.py: it cannot run here: `get_codings` begins by calling `viz_meta_codings_page`, which issues a live `dxpy.DXHTTPRequest` to the DNAnexus API (`resp["url"] + "/viz-meta/3.0/..."`); it needs network access and credentials, and the only
- `src/python/dxpy/dx_extract_utils/retrieve_bins.py::retrieve_bins` a: blocked — inputs.py: it cannot run here: `retrieve_bins` calls `dxpy.describe(project)` (a DNAnexus API request) and then shells out to the `dx` CLI (`subprocess.check_output(["dx", "cat", ...])`), both of which require network access and platform cre
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — verify.py: no_inputs; inputs.py: the generator failed: BrokenPipeError: [Errno 32] Broken pipe
- `src/python/dxpy/bindings/dxfile.py::DXFile._write2` a: blocked — inputs.py: it cannot run here: `DXFile._write2` performs remote file I/O against the DNAnexus API — its first step `self._ensure_write_bufsize(**kwargs)` queries the project's file-upload parameters from the server (the buffer size is explic
- `src/python/dxpy/bindings/dxfile.py::DXFile._read2` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::find_executions` a: blocked — inputs.py: it cannot run here: `find_executions` iterates over `dxpy.find_executions(**query)` (and may call `dxpy.api.job_describe` / `resolve_existing_path`), all of which make live requests to the DNAnexus API server; there is no input th
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` a: blocked — inputs.py: it cannot run here: `generate_batch_inputs` resolves a project/folder path and then calls `dxpy.api.system_generate_batch_inputs`, which issues an HTTP request to the DNAnexus platform API; the batch results it processes exist onl
- `src/python/dxpy/scripts/dx.py::get_database` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::run_body` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::run_body` b: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::watch` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::ssh` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::ssh` b: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::archive` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::archive` b: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/scripts/dx.py::cd` a: blocked — inputs.py: it cannot run here: `cd` resolves paths and describes projects through the DNAnexus API (`resolve_existing_path`, `dxpy.get_handler(...).describe`, `list_folder`), which all require network access and credentials to a remote servi
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` b: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/bindings/dxdatabase.py::DXDatabase.get_download_url` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/utils/executable_unbuilder.py::_dump_app_or_applet` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/nextflow/collect_images.py::_populate_cached_file_ids` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: blocked — inputs.py: it cannot run here: every non-trivial input makes the function query the DNAnexus platform API (`dxpy.DXApplet(...).project`, `dxpy.DXProject(...).region`, `dxpy.api.app_describe`, `dxpy.api.workflow_describe`) for each stage, so 
- `src/python/dxpy/executable_builder.py::get_valid_bill_to` a: blocked — inputs.py: it cannot run here: `get_valid_bill_to` always begins with `dxpy.whoami()` (an API call to the DNAnexus platform) and then calls `dxpy.api.user_describe` / `dxpy.api.org_describe`, which are remote server requests; no input can av
- `src/python/dxpy/cli/download.py::download` a: deferred — outside the 20 repairs measured; no repair submitted, inputs not obtained
