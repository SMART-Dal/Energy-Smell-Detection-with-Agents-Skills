# Energy report — dx-toolkit @ accd86a

154 units listed, 83 with an accepted suspicion · 24 repairs submitted, 77 deferred · 12 confirmed · 3 partial · 2 regressed · 3 negligible · 4 over_limit · 11 applied
Noise floor 1.8–7.9% (from: session calibration).

## Applied

### `src/python/dxpy/utils/pretty_print.py::flatten_json_array` — C1S4-flatten-subn (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +23.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| strings-300 | 67.01 | 56.45 | +15.8% | 1.1% | yes |
| strings-400 | 68.33 | 55.70 | +18.5% | 4.0% | yes |
| crlf-300 | 63.21 | 53.07 | +16.0% | 1.4% | yes |
| deep-inputspec | 86.28 | 47.81 | +44.6% | 0.6% | yes |

### `src/python/dxpy/utils/pretty_print.py::escape_unicode_string` — C8S2-escape-translate (C8.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +69.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-controls | 115.93 | 12.28 | +89.4% | 2.1% | yes |
| backslash-heavy | 116.82 | 37.50 | +67.9% | 0.1% | yes |
| mixed-random | 111.23 | 43.75 | +60.7% | 1.4% | yes |
| tabs-and-cr | 111.36 | 45.05 | +59.6% | 0.7% | yes |

### `src/python/dxpy/utils/resolver.py::get_last_pos_of_char` — C6S2-last-pos-rfind (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +58.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-escaped-slashes | 108.73 | 57.40 | +47.2% | 1.7% | yes |
| gapped-escaped | 119.49 | 18.93 | +84.2% | 0.0% | yes |
| gapped-random-escaped | 116.32 | 33.00 | +71.6% | 1.2% | yes |
| escaped-colons | 84.12 | 56.61 | +32.7% | 5.4% | yes |

### `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` — C3S5-first-pos-leftscan (C3.S5)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +88.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colons-dense | 117.03 | 0.05 | +100.0% | 0.0% | yes |
| all-escaped-stars | 117.60 | 56.44 | +52.0% | 6.5% | yes |
| mixed-escapes | 115.08 | 0.03 | +100.0% | 0.0% | yes |
| mostly-escaped | 113.01 | 0.02 | +100.0% | 0.0% | yes |

### `src/python/dxpy/utils/resolver.py::parse_input_keyval` — C1S4-keyval-name (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +56.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| dense-equals | 129.10 | 49.97 | +61.3% | 2.6% | yes |
| escaped-equals | 129.76 | 64.60 | +50.2% | 1.1% | yes |
| backslash-runs | 119.88 | 53.85 | +55.1% | 2.6% | yes |
| query-string | 109.48 | 45.60 | +58.4% | 2.6% | yes |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type` — C8S3-infer-genotype-locals (C8.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +10.1%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-loci-few-samples | 69.84 | 63.49 | +9.1% | 6.7% | yes |
| no-results | 68.46 | 60.61 | +11.5% | 3.0% | yes |
| mixed-medium | 70.97 | 62.67 | +11.7% | 0.8% | yes |
| many-loci-tiny-samples | 68.89 | 63.18 | +8.3% | 0.8% | yes |

### `src/python/dxpy/bindings/apollo/data_transformations.py::transform_to_expression_matrix` — C8S3-expression-matrix-locals (C8.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +14.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| dense-full | 54.70 | 46.93 | +14.2% | 2.4% | yes |
| many-samples | 59.40 | 50.97 | +14.2% | 1.1% | yes |
| few-samples-many-features | 60.71 | 51.80 | +14.7% | 3.8% | yes |
| duplicated-entries | 61.82 | 52.23 | +15.5% | 5.8% | yes |

### `src/python/dxpy/dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter` — C7S1-pheno-filter-noreduce (C7.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +59.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| in-large-values | 126.60 | 53.33 | +57.9% | 0.5% | yes |
| not-in-large-values | 72.76 | 61.28 | +15.8% | 10.5% | yes |
| exists-plus-in | 107.73 | 18.05 | +83.2% | 0.1% | yes |
| multi-compound-match-later | 108.02 | 22.30 | +79.4% | 0.5% | yes |

### `src/python/dxpy/nextflow/nextflow_templates.py::get_nextflow_src` — C10S4-nextflow-src-join (C10.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +10.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| files-200 | 67.21 | 59.36 | +11.7% | 10.4% | yes |
| strings-300-abs-resources | 68.28 | 62.67 | +8.2% | 1.2% | yes |
| mixed-150-file-heavy | 66.39 | 60.98 | +8.1% | 0.8% | yes |
| mixed-400-profile-resources | 68.77 | 59.01 | +14.2% | 0.1% | yes |

### `src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON` — C1S1-validate-json-schema (C1.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +100.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| case-4-allele | 108.00 | 0.03 | +100.0% | 0.1% | yes |
| case-5-variant | 107.32 | 0.02 | +100.0% | 0.0% | yes |
| case-6-allele | 106.82 | 0.01 | +100.0% | 0.1% | yes |
| case-7-variant | 109.67 | 0.01 | +100.0% | 0.0% | yes |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::filter_results` — C5S1-filter-results-set (C5.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +57.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-all-filtered | 72.89 | 56.16 | +23.0% | 1.0% | yes |
| large-mostly-filtered | 64.34 | 55.58 | +13.6% | 1.3% | yes |
| sample-id-filter | 105.17 | 5.69 | +94.6% | 0.2% | yes |
| big-restricted-list | 102.15 | 0.78 | +99.2% | 0.1% | yes |

## Confirmed, not applied

### `src/python/dxpy/utils/resolver.py::split_unescaped` — C6S2-split-unescaped-noslice (C6.S2)

**confirmed** — not applied: changes src/python/dxpy/utils/resolver.py::get_last_pos_of_char, which C6S2-last-pos-rfind already changes
Mean saving across its cases: +60.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colon-escaped | 113.88 | 39.45 | +65.4% | 0.4% | yes |
| spaces-escaped | 114.32 | 39.94 | +65.1% | 0.7% | yes |
| backslash-runs | 96.54 | 55.72 | +42.3% | 1.9% | yes |
| mixed-include-empty | 113.54 | 34.19 | +69.9% | 0.6% | yes |

## Measured, not confirmed

### `src/python/dxpy/utils/pretty_print.py::format_table` — C3S2-format-table-bar (C3.S2)

**negligible** — no case moved more than the noise: the largest reading was -5.2% +-5.6% on 'large-12col', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -1.7%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-12col | 55.66 | 58.54 | -5.2% | 5.6% | no: pairs disagree |
| narrow-truncation | 54.10 | 54.53 | -0.8% | 1.7% | no: pairs disagree |
| no-column-names | 56.89 | 58.28 | -2.4% | 3.0% | no: pairs disagree |
| many-duplicates | 55.48 | 54.50 | +1.8% | 4.8% | no: pairs disagree |

### `src/python/dxpy/utils/pretty_print.py::format_table` — C6S2-format-table-len (C6.S2)

**regressed** — the repair costs more than the code it replaces: 5.2% lost on 'large-12col', above the 1.8% noise floor, and no case improved. Worse on 3 of 4 cases ('large-12col', 'narrow-truncation', 'no-column-names').
Mean saving across its cases: -3.7%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-12col | 57.23 | 60.23 | -5.2% | 2.0% | yes |
| narrow-truncation | 54.42 | 55.68 | -2.3% | 1.0% | yes |
| no-column-names | 54.68 | 57.20 | -4.6% | 3.4% | yes |
| many-duplicates | 53.43 | 54.82 | -2.6% | 2.6% | no: pairs disagree |

### `src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink` — C4S7-dxlink-guard (C4.S7)

**partial** — saves energy on 1 of 4 inputs ('big-array-no-link'; best 100.0% +-0.1% on 'big-array-no-link'), and no saving that can be told from noise on the rest: 'big-dict-no-link' +0.6% +-0.6% (its pairs disagree too much to tell); 'link-dict-pid' -0.0% +-0.8% (its pairs disagree too much to tell); 'link-dict-partial' -0.8% +-0.6% (within the 1.8% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +24.9%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-dict-no-link | 53.54 | 53.22 | +0.6% | 0.6% | no: pairs disagree |
| big-array-no-link | 104.87 | 0.04 | +100.0% | 0.1% | yes |
| link-dict-pid | 53.20 | 53.22 | -0.0% | 0.8% | no: pairs disagree |
| link-dict-partial | 53.06 | 53.48 | -0.8% | 0.6% | no: within the floor |

### `src/python/dxpy/utils/spelling_corrector.py::correct` — C1S4-correct-edits1 (C1.S4)

**negligible** — no case moved more than the noise: the largest reading was +2.2% +-6.0% on 'no-hit-len11', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.3%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| edit2-hit-len12 | 61.80 | 61.12 | +1.1% | 2.1% | no: pairs disagree |
| edit2-hit-len13 | 54.70 | 54.48 | +0.4% | 3.2% | no: pairs disagree |
| no-hit-len11 | 58.07 | 56.76 | +2.3% | 6.0% | no: pairs disagree |
| no-hit-len13 | 60.70 | 59.90 | +1.3% | 1.7% | no: pairs disagree |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_results` — C10S2-harmonize-results-get (C10.S2)

**regressed** — the repair costs more than the code it replaces: 12.2% lost on 'large', above the 7.9% noise floor, and no case improved. Worse on 3 of 4 cases ('wide-fields', 'many-results', 'large').
Mean saving across its cases: -8.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-fields | 57.63 | 62.36 | -8.2% | 3.4% | yes |
| many-results | 57.45 | 64.03 | -11.4% | 11.4% | yes |
| dense | 57.94 | 58.85 | -1.6% | 0.5% | no: within the floor |
| large | 58.41 | 65.53 | -12.2% | 5.5% | yes |

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — C5S2-coding-display-index (C5.S2)

**negligible** — no case moved more than the noise: the largest reading was -2.3% +-4.2% on 'hier-large', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -1.0%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 77.69 | 79.42 | -2.2% | 4.2% | no: pairs disagree |
| hier-wide | 76.50 | 77.10 | -0.8% | 2.2% | no: pairs disagree |
| hier-paginated | 72.52 | 73.92 | -1.9% | 2.8% | no: pairs disagree |
| hier-no-concepts | 73.44 | 72.65 | +1.1% | 3.1% | no: pairs disagree |

### `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec` — C6S2-cluster-spec-filter-first (C6.S2)

**partial** — saves energy on 1 of 4 inputs ('many-entrypoints-no-clusterspec'; best 99.8% +-0.0% on 'many-entrypoints-no-clusterspec'), and no saving that can be told from noise on the rest: 'wildcard-large-appdoc' -2.3% +-4.2% (its pairs disagree too much to tell); 'fallback-to-app-wildcard' +1.4% +-3.0% (its pairs disagree too much to tell); 'field-heavy-clusterspec' +2.5% +-13.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +25.4%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wildcard-large-appdoc | 53.72 | 54.97 | -2.3% | 4.2% | no: pairs disagree |
| fallback-to-app-wildcard | 51.84 | 51.13 | +1.4% | 3.0% | no: pairs disagree |
| many-entrypoints-no-clusterspec | 105.02 | 0.18 | +99.8% | 0.1% | yes |
| field-heavy-clusterspec | 56.72 | 55.27 | +2.5% | 13.0% | no: pairs disagree |

### `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` — C5S1-custom-inputs-required-set (C5.S1)

**partial** — saves energy on 1 of 4 inputs ('all-required'; best 6.1% +-3.6% on 'all-required'), and no saving that can be told from noise on the rest: 'union-types' +2.9% +-8.2% (its pairs disagree too much to tell); 'path-formats' +2.8% +-3.3% (its pairs disagree too much to tell); 'many-definitions' -3.0% +-4.1% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.2%.
Measured twice: the first measurement came out `inconclusive` with an input too noisy to read, and this is the second.
The agent measured `mixed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-required | 63.54 | 59.68 | +6.1% | 3.6% | yes |
| union-types | 62.03 | 60.24 | +2.9% | 8.2% | no: pairs disagree |
| path-formats | 58.83 | 57.17 | +2.8% | 3.3% | no: pairs disagree |
| many-definitions | 58.10 | 59.83 | -3.0% | 4.1% | no: pairs disagree |

## Not measured

### `src/python/dxpy/cli/output_handling.py::write_expression_output` — C3S2-expression-output-colset (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` — C3S3-custom-inputs-type-tables (C3.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/cli/exec_io.py::ExecutableInputs.add` — C4S6-exec-input-json-guard (C4.S6)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/bindings/dxworkflow.py::DXWorkflow._get_stage_id` — C3S5-stage-id-any (C3.S5)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` b: deferred — a different edit (bounded rfind inside the same right-to-left walk) from the submitted left-to-right scan; not written or measured, and the submitted repair removes the loop it would have improved
- `src/python/dxpy/utils/resolver.py::resolve_path` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/resolver.py::resolve_job_ref` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/resolver.py::_validate_resolution_output_length` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/resolver.py::_resolve_folder` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/spelling_corrector.py::_edits1` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/describe.py::print_data_obj_desc` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/describe.py::print_data_obj_desc` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/completer.py::get_folder_matches` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/completer.py::ListCompleter.get_matches` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/completer.py::DXAppCompleter._populate_matches` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/local_exec_utils.py::get_implicit_depends_on` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/file_load_utils.py::get_job_input_filenames` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/file_load_utils.py::get_job_input_filenames` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/file_load_utils.py::get_input_spec_patterns` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/utils/executable_unbuilder.py::_dump_app_or_applet` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` b: deferred — nested generator repair needs a shared display counter threaded through the recursion; not written or measured
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::get_assay_name_info` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::extract_dataset` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::csv_from_json` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/dataset_utilities.py::csv_from_json` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — inputs.py: the generator failed: BrokenPipeError: [Errno 32] Broken pipe (twice); verify.py: no_inputs for C3S2-expression-output-colset
- `src/python/dxpy/cli/download.py::download` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/download.py::download` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/cli/exec_io.py::ExecutableInputs.add` a: deferred — submitted as C4S6-exec-input-json-guard but verify.py returned over_limit: 20 repairs already had a verdict
- `src/python/dxpy/cli/exec_io.py::ExecutableInputs.add` b: deferred — the set needs to become a module constant to stop being rebuilt, which lies outside the function; not measured
- `src/python/dxpy/cli/parsers.py::PrintInstanceTypeHelp.__call__` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type` b: blocked — the repair (`result_entries.extend(inferred_entries)`) mutates the caller's list, which changes the unit's effect on its arguments; it cannot be made to behave identically
- `src/python/dxpy/dx_extract_utils/germline_utils.py::_harmonize_sql_select_named_expression` a: deferred — no small edit found: `re.sub` replaces every match while the second scan is an anchored `re.match`, so one cannot stand in for the other
- `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_sql` a: deferred — inputs not requested; repair (read the return-columns file once per process) not written within the time
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` a: deferred — inputs were generated but the repair was not written within the time
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::retrieve_geno_bins` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::somatic_final_payload` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/dx_extract_utils/input_validation.py::validate_filter` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_names_list` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.describe_underlying_workflow` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/download_all_inputs.py::_gen_helper_dict` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/mount_all_inputs.py::mount_all_inputs` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/search.py::_find` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxfile.py::DXFile.upload_part` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxfile_functions.py::_download_dxfile` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/dxworkflow.py::DXWorkflow._get_stage_id` a: blocked — inputs.py: only 0 of 8 generated inputs ran and repeated on the original code (DXError: This DXWorkflow handler has not been initialized with a workflow ID and cannot be described); the submission C3S5-stage-id-any also came back over_limit
- `src/python/dxpy/bindings/dxworkflow.py::DXWorkflow.get_stage` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/bindings/__init__.py::DXDataObject._get_creation_params` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::archive` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::find_executions` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::get_database` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::rm` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::run_body` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::run_body` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx.py::tree` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/__init__.py::_get_pool_manager` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/__init__.py::DXHTTPRequest` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` a: deferred — inputs were generated; the candidate edit (move `message.encode` below the early return) stops raising UnicodeEncodeError for short messages with lone surrogates, so it is not behaviour-preserving and was not submitted
- `src/python/dxpy/app_builder.py::upload_resources` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/app_builder.py::upload_applet` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/app_builder.py::upload_applet` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/app_builder.py::_create_app` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/app_builder.py::_create_app` b: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/workflow_builder.py::_build_global_workflow` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/executable_builder.py::get_permitted_regions` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/ssh_tunnel_app_support.py::get_notebook_app_versions` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx_build_app.py::_check_file_syntax` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/nextflow/nextflow_utils.py::_load_versions_manifest` a: deferred — inputs were generated but the repair was not written: test_nextflow.py patches the manifest file contents between calls, so a per-process cache would change behaviour the tests rely on
- `src/python/dxpy/nextflow/nextflow_builder.py::prepare_nextflow` a: deferred — accepted but outside the 20 repairs measured: its unit was not asked for inputs (it reaches the network, a service, or interactive input, or its saving was too small to rank in the first 20)
- `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` b: deferred — submitted as C3S3-custom-inputs-type-tables but verify.py returned over_limit: 20 repairs already had a verdict
