# Energy report — dx-toolkit @ accd86a

244 units listed, 178 with an accepted suspicion · 26 repairs submitted, 197 deferred · 11 confirmed · 2 partial · 2 mixed · 2 regressed · 3 negligible · 6 over_limit · 11 applied
Noise floor 1.2% (from: session calibration).

## Applied

### `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` — C3S5-first-pos (C3.S5)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +88.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colons-dense | 114.22 | 0.03 | +100.0% | 0.1% | yes |
| all-escaped-stars | 117.98 | 52.72 | +55.3% | 0.0% | yes |
| mixed-escapes | 118.81 | 0.05 | +100.0% | 0.0% | yes |
| mostly-escaped | 115.74 | 0.03 | +100.0% | 0.1% | yes |

### `src/python/dxpy/utils/resolver.py::get_last_pos_of_char` — C6S2-last-pos (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +65.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-escaped-slashes | 110.53 | 47.88 | +56.7% | 0.2% | yes |
| gapped-escaped | 118.50 | 17.08 | +85.6% | 0.2% | yes |
| gapped-random-escaped | 114.07 | 29.09 | +74.5% | 0.2% | yes |
| escaped-colons | 104.54 | 56.70 | +45.8% | 2.5% | yes |

### `src/python/dxpy/utils/resolver.py::split_unescaped` — C7S1-split-unescaped (C7.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +69.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colon-escaped | 112.50 | 26.99 | +76.0% | 0.9% | yes |
| spaces-escaped | 113.55 | 27.47 | +75.8% | 0.1% | yes |
| backslash-runs | 99.37 | 54.76 | +44.9% | 0.4% | yes |
| mixed-include-empty | 111.12 | 23.03 | +79.3% | 0.3% | yes |

### `src/python/dxpy/utils/resolver.py::escape_folder_str` — C10S1-escape-folder (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +57.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-specials | 115.46 | 18.96 | +83.6% | 0.8% | yes |
| random-mixed | 98.23 | 59.08 | +39.9% | 2.8% | yes |
| dense-escapes | 118.70 | 40.62 | +65.8% | 0.9% | yes |
| unicode-mixed | 97.38 | 58.67 | +39.8% | 1.1% | yes |

### `src/python/dxpy/utils/pretty_print.py::flatten_json_array` — C1S4-flatten-subn (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +22.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| strings-300 | 70.00 | 60.24 | +13.9% | 3.1% | yes |
| strings-400 | 66.93 | 55.50 | +17.1% | 1.1% | yes |
| crlf-300 | 66.47 | 56.27 | +15.3% | 0.2% | yes |
| deep-inputspec | 98.44 | 54.58 | +44.6% | 0.2% | yes |

### `src/python/dxpy/utils/pretty_print.py::escape_unicode_string` — C10S1-escape-unicode (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +68.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-controls | 108.08 | 12.99 | +88.0% | 0.7% | yes |
| backslash-heavy | 111.65 | 35.79 | +67.9% | 0.3% | yes |
| mixed-random | 109.70 | 44.27 | +59.6% | 0.3% | yes |
| tabs-and-cr | 111.54 | 45.85 | +58.9% | 0.2% | yes |

### `src/python/dxpy/utils/__init__.py::normalize_timedelta` — C4S6-timedelta-suffix (C4.S6)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +53.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| suffix-s | 104.59 | 48.72 | +53.4% | 0.6% | yes |
| suffix-h | 108.16 | 51.62 | +52.3% | 3.5% | yes |
| suffix-d | 109.92 | 51.40 | +53.2% | 0.1% | yes |
| suffix-y | 108.77 | 51.05 | +53.1% | 0.2% | yes |

### `src/python/dxpy/nextflow/nextflow_templates.py::get_nextflow_src` — C10S4-nextflow-src-join (C10.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +6.8%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| files-200 | 59.69 | 55.50 | +7.0% | 2.9% | yes |
| strings-300-abs-resources | 60.68 | 56.18 | +7.4% | 0.4% | yes |
| mixed-150-file-heavy | 58.95 | 55.52 | +5.8% | 0.4% | yes |
| mixed-400-profile-resources | 60.92 | 56.58 | +7.1% | 1.5% | yes |

### `src/python/dxpy/utils/local_exec_utils.py::has_local_job_refs` — C1S4-localrefs-bind (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +7.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| nonlocal-refs-only | 61.33 | 56.92 | +7.2% | 1.5% | yes |
| big-list | 65.03 | 61.47 | +5.5% | 1.2% | yes |
| deep-tree | 64.75 | 58.81 | +9.2% | 3.1% | yes |
| many-small-dicts | 64.65 | 59.40 | +8.1% | 3.6% | yes |

### `src/python/dxpy/utils/__init__.py::_dict_raise_on_duplicates` — C10S1-dupkeys-dict (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +36.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| strings-90k | 82.34 | 53.39 | +35.2% | 2.7% | yes |
| ints-90k | 86.87 | 54.19 | +37.6% | 0.8% | yes |
| list-pairs-90k | 84.66 | 55.32 | +34.7% | 1.1% | yes |
| nested-tuples-50k | 89.17 | 54.60 | +38.8% | 0.8% | yes |

### `src/python/dxpy/utils/pathmatch.py::translate` — C10S4-glob-translate-join (C10.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +17.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| literal-long | 64.00 | 53.60 | +16.3% | 0.5% | yes |
| many-questions | 68.89 | 55.67 | +19.2% | 2.8% | yes |
| unclosed-bracket | 65.50 | 55.05 | +16.0% | 1.7% | yes |
| mixed | 67.36 | 54.75 | +18.7% | 0.6% | yes |

## Measured, not confirmed

### `src/python/dxpy/utils/resolver.py::is_glob_pattern` — C4S7-is-glob (C4.S7)

**mixed** — a trade-off, not a fix: 5.7% saved on 'very-dense-mixed-10000' but 1.7% lost on 'dense-mixed-8000', both clearing the 1.2% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +1.3%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `regressed`; re-measured `mixed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| star-unescaped-start-6000 | 59.38 | 58.85 | +0.9% | 3.6% | no: pairs disagree |
| question-unescaped-start-6000 | 59.21 | 59.06 | +0.3% | 1.2% | no: pairs disagree |
| dense-mixed-8000 | 59.04 | 60.02 | -1.7% | 0.9% | yes |
| very-dense-mixed-10000 | 62.95 | 59.34 | +5.7% | 0.2% | yes |

### `src/python/dxpy/utils/pretty_print.py::format_table` — C6S3-table-first-row (C6.S3)

**regressed** — the repair costs more than the code it replaces: 2.2% lost on 'no-column-names', above the 1.2% noise floor, and no case improved. Worse on 3 of 4 cases ('narrow-truncation', 'no-column-names', 'many-duplicates').
Mean saving across its cases: -2.1%.
The agent measured `negligible`; re-measured `regressed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-12col | 59.82 | 61.15 | -2.2% | 3.6% | no: pairs disagree |
| narrow-truncation | 57.67 | 58.97 | -2.3% | 1.0% | yes |
| no-column-names | 56.94 | 58.20 | -2.2% | 0.9% | yes |
| many-duplicates | 59.25 | 60.22 | -1.6% | 0.8% | yes |

### `src/python/dxpy/utils/pretty_print.py::format_table` — C3S2-table-border (C3.S2)

**partial** — saves energy on 1 of 4 inputs ('many-duplicates'; best 2.3% +-1.4% on 'many-duplicates'), and no saving that can be told from noise on the rest: 'large-12col' +0.6% +-0.6% (its pairs disagree too much to tell); 'narrow-truncation' +0.4% +-0.8% (its pairs disagree too much to tell); 'no-column-names' +0.7% +-1.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +1.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-12col | 59.33 | 58.98 | +0.6% | 0.6% | no: pairs disagree |
| narrow-truncation | 58.27 | 58.03 | +0.4% | 0.8% | no: pairs disagree |
| no-column-names | 56.81 | 56.39 | +0.7% | 1.8% | no: pairs disagree |
| many-duplicates | 59.78 | 58.43 | +2.3% | 1.4% | yes |

### `src/python/dxpy/utils/spelling_corrector.py::_edits1` — C6S2-edits1-set (C6.S2)

**negligible** — no case moved more than the noise: the largest reading was -1.7% +-3.3% on 'word-400-mixed', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| word-90 | 54.03 | 53.91 | +0.2% | 0.9% | no: pairs disagree |
| word-150 | 61.52 | 62.04 | -0.9% | 0.3% | no: within the floor |
| word-260 | 54.95 | 54.69 | +0.5% | 0.6% | no: pairs disagree |
| word-400-mixed | 53.64 | 54.55 | -1.7% | 3.3% | no: pairs disagree |

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — C4S7-truncate-guard (C4.S7)

**negligible** — no case moved more than the noise: the largest reading was -0.2% +-0.3% on 'mixed-30k', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| control-20k | 77.76 | 77.83 | -0.1% | 1.2% | no: pairs disagree |
| two-byte-20k | 57.49 | 57.44 | +0.1% | 0.2% | no: pairs disagree |
| four-byte-20k | 57.51 | 57.59 | -0.2% | 0.3% | no: pairs disagree |
| mixed-30k | 65.38 | 65.49 | -0.2% | 0.3% | no: pairs disagree |

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — C3S4-coding-display-index (C3.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.8% +-2.8% on 'hier-wide', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 72.17 | 72.53 | -0.5% | 1.4% | no: pairs disagree |
| hier-wide | 74.30 | 73.67 | +0.8% | 2.8% | no: pairs disagree |
| hier-paginated | 72.35 | 72.47 | -0.2% | 1.9% | no: pairs disagree |
| hier-no-concepts | 69.55 | 69.15 | +0.6% | 3.6% | no: pairs disagree |

### `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` — C8S1-final-payload-columns (C8.S1)

**partial** — saves energy on 3 of 4 inputs ('allele-ordered', 'allele-unordered', 'annotation-unordered'; best 4.1% +-4.0% on 'allele-ordered'), and no saving that can be told from noise on the rest: 'annotation-ordered' +2.6% +-2.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| allele-ordered | 56.72 | 54.39 | +4.1% | 4.0% | yes |
| allele-unordered | 54.34 | 52.26 | +3.8% | 0.5% | yes |
| annotation-ordered | 54.31 | 52.89 | +2.6% | 2.7% | no: pairs disagree |
| annotation-unordered | 53.99 | 52.06 | +3.6% | 0.6% | yes |

### `src/python/dxpy/nextflow/nextflow_utils.py::_load_versions_manifest` — C8S1-versions-manifest (C8.S1)

**regressed** — the repair costs more than the code it replaces: 265.6% lost on 'many-minimal', above the 1.2% noise floor, and no case improved. Worse on 4 of 4 cases ('many-minimal', 'many-with-extras', 'unicode-heavy', 'varied-digest').
Mean saving across its cases: -232.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-minimal | 32.74 | 119.69 | -265.5% | 21.6% | yes |
| many-with-extras | 28.43 | 111.37 | -291.7% | 31.0% | yes |
| unicode-heavy | 51.72 | 112.43 | -117.4% | 0.8% | yes |
| varied-digest | 34.24 | 121.37 | -254.5% | 9.9% | yes |

### `src/python/dxpy/bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range` — C1S4-range-int-once (C1.S4)

**mixed** — a trade-off, not a fix: 33.5% saved on 'string-values-80k' but 14.5% lost on 'each-separately-over-window', both clearing the 1.2% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +15.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-100k | 73.16 | 57.44 | +21.5% | 2.2% | yes |
| each-separately-over-window | 58.86 | 67.39 | -14.5% | 6.1% | yes |
| string-values-80k | 87.68 | 58.28 | +33.5% | 2.1% | yes |
| global-window-violation | 70.46 | 54.46 | +22.7% | 1.4% | yes |

## Not measured

### `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_sql` — C8S1-harmonize-columns (C8.S1)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec` — C7S4-cluster-filter-first (C7.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/utils/completer.py::ListCompleter.get_matches` — C1S4-listcompleter-rfind (C1.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/cli/output_handling.py::write_expression_output` — C3S2-expr-output-set (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink` — C4S6-dxlink-guard (C4.S6)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` — C7S1-cohort-ids-comprehension (C7.S1)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/utils/resolver.py::get_first_pos_of_char` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::split_unescaped` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::is_container_id` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink` a: deferred — outside the 20 repairs measured (verify.py reported over_limit); repair written as submission C4S6-dxlink-guard
- `src/python/dxpy/utils/resolver.py::resolve_path` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::parse_input_keyval` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::resolve_container_id_or_name` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/resolver.py::_validate_resolution_output_length` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/pretty_print.py::escape_unicode_string` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/pretty_print.py::flatten_json_array` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/pretty_print.py::flatten_json_array` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/pretty_print.py::format_table` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/spelling_corrector.py::_edits1` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/spelling_corrector.py::_known_edits2` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/spelling_corrector.py::correct` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/spelling_corrector.py::correct` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/pathmatch.py::filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/__init__.py::group_array_by_field` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dxlog.py::DXLogHandler.__init__` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/config.py::DXConfig.clear` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/config.py::DXConfig.__len__` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::get_io_spec` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::print_data_obj_desc` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::print_data_obj_desc` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::print_project_desc` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::get_resolved_jbors` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/describe.py::locale_from_currency_code` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/printing.py::fill` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/batch_utils.py::batch_launch_args` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/batch_utils.py::batch_launch_args` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/file_load_utils.py::filter_dict` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/file_load_utils.py::get_job_input_filenames` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/file_load_utils.py::analyze_bash_vars` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/file_load_utils.py::get_input_spec_patterns` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/exec_utils.py::DXExecDependencyInstaller.generate_shellcode` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/exec_utils.py::entry_point` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/exec_utils.py::parse_args_as_job_input` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/exec_utils.py::convert_handlers_to_dxlinks` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/local_exec_utils.py::get_nonclosed_data_obj_link` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/local_exec_utils.py::run_one_entry_point` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/local_exec_utils.py::run_one_entry_point` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/local_exec_utils.py::resolve_job_references` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/local_exec_utils.py::run_entry_points` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/executable_unbuilder.py::_dump_app_or_applet` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/executable_unbuilder.py::_dump_app_or_applet` d: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/completer.py::get_folder_matches` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/completer.py::ListCompleter.get_matches` a: deferred — outside the 20 repairs measured (verify.py reported over_limit); repair written as submission C1S4-listcompleter-rfind
- `src/python/dxpy/utils/completer.py::DXAppCompleter._populate_matches` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/completer.py::LocalCompleter._populate_matches` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/utils/job_log_client.py::metrics_top` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.descriptor_file_dict` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_names_list` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/data_transformations.py::transform_to_expression_matrix` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.__init__` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.parse_list_v1` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.parse_v1` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.convert_to_between_operator` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.build_partial_overlap_genobin_filters` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/vizserver_filters_from_json_parser.py::JSONFiltersValidator.merge_duplicate_filters` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/cmd_line_options_validator.py::ArgsValidator.interpret_mutually_exclusive_group` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/apollo/cmd_line_options_validator.py::ArgsValidator.interpret_exclusive_with_exceptions` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::location_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::generate_assay_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::retrieve_geno_bins` a: blocked — inputs.py: it cannot run here: `retrieve_geno_bins` delegates its entire workload to `retrieve_bins(...)`, which needs a DNAnexus `project` to fetch the gene manifest data objects from the platform (network/API access); no input can avoid that lookup.
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::retrieve_geno_bins` b: blocked — inputs.py: it cannot run here: `retrieve_geno_bins` delegates its entire workload to `retrieve_bins(...)`, which needs a DNAnexus `project` to fetch the gene manifest data objects from the platform (network/API access); no input can avoid that lookup.
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::location_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::basic_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::generate_assay_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/somatic_filter_payload.py::somatic_final_payload` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_sql` a: deferred — outside the 20 repairs measured (verify.py reported over_limit); repair written as submission C8S1-harmonize-columns
- `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_sql` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::_harmonize_sql_select_named_expression` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::_harmonize_sql_select_named_expression` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_results` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::sort_germline_variant` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/cohort_filter_payload.py::generate_pheno_filter` a: blocked — inputs.py: the inputs that run here reach only 39% of the function (lines 10, 17, 22, 29, 31, 41, 47, 50-56, 58-59, 62-69, 71-72, 75, ... never ran), so they would not measure its real work. Also no behaviour-preserving repair exists inside this unit: the converter is an opaque callable, and the quadratic accumulation is created in validate_cohort_ids.
- `src/python/dxpy/dx_extract_utils/retrieve_bins.py::retrieve_bins` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation.py::is_list_of_strings` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation.py::validate_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation.py::validate_filter` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation_somatic.py::validate_somatic_filter` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation_somatic.py::validate_somatic_filter` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/input_validation_somatic.py::is_list_of_strings` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: blocked — inputs.py: it cannot run here: `validate_cohort_ids` performs its work by calling `raw_api_call`, which issues a live HTTP POST to a Vizserver (`dxpy.DXHTTPRequest`); the function cannot complete without network access to that remote service. A repair was written (build id_list with `[convert(b) for b in ids]` where `convert` is int, float or str, keeping the returned lambda) but could not be measured.
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::get_assay_name_info` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::get_assay_name_info` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::get_assay_name_info` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::get_codings` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_entity_dframe` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::csv_from_json` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::csv_from_json` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_dataset` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_dataset` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::json_validation_function` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::retrieve_entities` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_somatic` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_germline` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — inputs.py: no inputs could be generated for src/python/dxpy/cli/output_handling.py::write_expression_output: the generator failed: BrokenPipeError: [Errno 32] Broken pipe (three attempts). A repair was written (build `expected_columns = set(COLUMN_NAMES)` once and compare each row's key set with it) as submission C3S2-expr-output-set, which verify.py did not measure.
- `src/python/dxpy/cli/download.py::_download_folders` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/cp.py::cp_to_noexistent_destination` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/cli/org.py::get_user_id` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxdatabase.py::DXDatabase.get_download_url` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile_functions.py::_download_dxfile` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile_functions.py::download_dxfile` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile_functions.py::list_subfolders` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile_functions.py::download_folder` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile_functions.py::upload_local_file` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile.py::DXFile.write` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile.py::DXFile._write2` a: blocked — inputs.py: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: DXError: This DXFile handler has not been initialized with a file ID and cannot be described)
- `src/python/dxpy/bindings/dxfile.py::DXFile._write2` b: blocked — inputs.py: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: DXError: This DXFile handler has not been initialized with a file ID and cannot be described)
- `src/python/dxpy/bindings/dxfile.py::DXFile.upload_part` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile.py::DXFile.__iter__` a: blocked — inputs.py: it cannot run here: `DXFile.__iter__` calls `self.read(self._read_bufsize)` on a remote file handler; `DXFile.read` fetches the file's download URL and data from the DNAnexus API over the network (and needs `describe` for the file length), so no input can make it run without network access.
- `src/python/dxpy/bindings/dxfile.py::DXFile._read2` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/__init__.py::DXDataObject._wait_until_parts_uploaded` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxfile.py::_get_write_buf_size` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.describe_underlying_workflow` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/download_all_inputs.py::_gen_helper_dict` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/download_all_inputs.py::download_all_inputs` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/mount_all_inputs.py::_gen_helper_dict` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/search.py::_find` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/search.py::_find` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxworkflow.py::DXWorkflow._get_stage_id` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/__init__.py::verify_string_dxid` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/__init__.py::DXDataObject.set_ids` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxdataobject_functions.py::describe` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxapplet.py::DXExecutable._get_run_input_common_fields` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/bindings/dxapp.py::DXApp.update` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/__init__.py::DXHTTPRequest` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/__init__.py::DXHTTPRequest` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/__init__.py::_get_pool_manager` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/__init__.py::_get_env_var_proxy` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/__init__.py::_debug_print_request` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/system_requirements.py::SystemRequirementsDict.__init__` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec` a: deferred — outside the 20 repairs measured (verify.py reported over_limit); repair written as submission C7S4-cluster-filter-first
- `src/python/dxpy/system_requirements.py::SystemRequirementsDict._add_dict_values` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_spec` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/app_builder.py::upload_resources` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/app_builder.py::upload_resources` d: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/app_builder.py::is_link_local` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/app_builder.py::build` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/executable_builder.py::verify_developer_rights` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/executable_builder.py::assert_consistent_reg_options` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/workflow_builder.py::_build_global_workflow` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/ssh_tunnel_app_support.py::poll_for_server_running` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/ssh_tunnel_app_support.py::get_notebook_app_versions` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::build_and_upload_locally` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::_check_file_syntax` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::_check_file_syntax` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::_lint` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::_build_app` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx_build_app.py::_verify_app_source_dir_impl` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/collect_images.py::_populate_cached_file_ids` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/ImageRef.py::ImageRef._dx_file_get_name` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/ImageRefFactory.py::ImageRefFactory.__init__` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/nextflow_builder.py::build_pipeline_with_npi` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/nextflow_builder.py::build_pipeline_with_npi` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/nextflow_builder.py::prepare_nextflow` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/nextflow/nextflow_utils.py::find_readme` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/templating/utils.py::create_files_from_templates` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/templating/python.py::get_strings` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/templating/python.py::get_strings` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/templating/python.py::get_output_fmt` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::rm` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::rm` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::upload_one` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::find_executions` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::find_executions` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::find_executions` d: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::get_database` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::run_body` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::run_body` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::cd` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::ssh` c: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::tree` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::get_output_path` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::wait` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::print_run_help` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::print_run_help` b: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::ls` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/scripts/dx.py::archive` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::filter_results` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
- `src/python/dxpy/dx_extract_utils/germline_utils.py::get_types_to_filter_out_when_infering` a: deferred — accepted, not measured: outside the 20 repairs measured or not submitted (a different edit to the same code as a submitted repair, or inputs not requested)
