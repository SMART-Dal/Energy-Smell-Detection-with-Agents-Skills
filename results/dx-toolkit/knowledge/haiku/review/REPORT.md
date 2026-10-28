# Energy report — dx-toolkit @ accd86a

77 units listed, 70 with an accepted suspicion · 9 repairs submitted, 63 deferred · 5 confirmed · 1 partial · 3 negligible · 5 applied
Noise floor 1.1% (from: session calibration).

## Applied

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — C7S1-truncate-bisect (C7.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| control-20k | 109.01 | 0.16 | +99.9% | 0.0% | yes |
| two-byte-20k | 110.26 | 0.30 | +99.7% | 0.1% | yes |
| four-byte-20k | 103.13 | 0.41 | +99.6% | 0.0% | yes |
| mixed-30k | 102.87 | 0.44 | +99.6% | 0.1% | yes |

### `src/python/dxpy/dx_extract_utils/filter_to_payload.py::validate_JSON` — C1S1-validate-json-dead-read (C1.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +100.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| case-4-allele | 113.41 | 0.02 | +100.0% | 0.1% | yes |
| case-5-variant | 113.77 | 0.02 | +100.0% | 0.0% | yes |
| case-6-allele | 114.46 | 0.03 | +100.0% | 0.0% | yes |
| case-7-variant | 110.22 | 0.01 | +100.0% | 0.1% | yes |

### `src/python/dxpy/dx_extract_utils/input_validation.py::is_list_of_strings` — C3S2-list-of-strings-hoist (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +26.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-strings-200k | 77.59 | 56.62 | +27.0% | 0.7% | yes |
| all-strings-100k-long | 76.14 | 56.42 | +25.9% | 1.6% | yes |
| nonstring-at-end | 76.92 | 56.40 | +26.7% | 1.1% | yes |
| nonstring-in-middle | 74.69 | 53.96 | +27.8% | 2.2% | yes |

### `src/python/dxpy/dx_extract_utils/input_validation_somatic.py::is_list_of_strings` — C3S2-list-of-strings-hoist-somatic (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +26.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-strings-250k | 77.78 | 57.27 | +26.4% | 1.0% | yes |
| unicode-strings-120k | 76.57 | 56.73 | +25.9% | 0.6% | yes |
| empty-strings-250k | 77.43 | 56.65 | +26.8% | 0.6% | yes |
| nonstr-at-end-150k | 77.49 | 57.35 | +26.0% | 1.8% | yes |

### `src/python/dxpy/dx_extract_utils/input_validation.py::validate_infer_flags` — C1S6-infer-flags-lazy-message (C1.S6)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +69.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| no-infer-mixed | 68.63 | 19.65 | +71.4% | 3.9% | yes |
| no-infer-mixed-2 | 66.45 | 18.44 | +72.2% | 1.3% | yes |
| infer-ref-valid | 77.89 | 25.70 | +67.0% | 0.4% | yes |
| infer-nocall-valid | 72.12 | 22.67 | +68.6% | 0.5% | yes |

## Measured, not confirmed

### `src/python/dxpy/bindings/search.py::_find` — C3S5-find-extra-page (C3.S5)

**partial** — saves energy on 2 of 4 inputs ('kwarg-project', 'big-pages'; best 3.0% +-2.8% on 'kwarg-project'), and no saving that can be told from noise on the rest: 'large-pages' +0.2% +-1.6% (its pairs disagree too much to tell); 'capped-limit' +1.6% +-2.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +1.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-pages | 57.73 | 57.61 | +0.2% | 1.6% | no: pairs disagree |
| capped-limit | 58.05 | 57.11 | +1.6% | 2.8% | no: pairs disagree |
| kwarg-project | 58.94 | 57.18 | +3.0% | 2.8% | yes |
| big-pages | 58.42 | 57.28 | +1.9% | 0.9% | yes |

### `src/python/dxpy/utils/spelling_corrector.py::correct` — C1S4-correct-edits-once (C1.S4)

**negligible** — no case moved more than the noise: the largest reading was -0.8% +-0.2% on 'no-hit-len13', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| edit2-hit-len12 | 65.23 | 65.63 | -0.6% | 0.4% | no: within the floor |
| edit2-hit-len13 | 57.97 | 58.04 | -0.1% | 1.4% | no: pairs disagree |
| no-hit-len11 | 61.19 | 61.32 | -0.2% | 0.3% | no: pairs disagree |
| no-hit-len13 | 64.47 | 65.01 | -0.8% | 0.2% | no: within the floor |

### `src/python/dxpy/dx_extract_utils/germline_utils.py::harmonize_germline_sql` — C8S2-harmonize-cached-columns (C8.S2)

**negligible** — no case moved more than the noise: the largest reading was +3.7% +-17.4% on 'large-select', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.8%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
The agent measured `regressed`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-select | 63.91 | 61.57 | +3.7% | 17.4% | no: pairs disagree |
| all-return-columns | 53.04 | 53.13 | -0.2% | 1.0% | no: pairs disagree |
| no-return-columns | 52.55 | 52.58 | -0.1% | 1.3% | no: pairs disagree |
| long-where | 53.35 | 53.39 | -0.1% | 0.4% | no: pairs disagree |

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — C3S4-coding-display-index-dict (C3.S4)

**negligible** — no case moved more than the noise: the largest reading was -0.5% +-3.1% on 'hier-paginated', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.1%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 74.02 | 74.36 | -0.5% | 2.0% | no: pairs disagree |
| hier-wide | 77.63 | 77.31 | +0.4% | 2.8% | no: pairs disagree |
| hier-paginated | 74.53 | 74.93 | -0.5% | 3.1% | no: pairs disagree |
| hier-no-concepts | 72.72 | 72.61 | +0.2% | 0.2% | no: pairs disagree |

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/scripts/dx.py::DXCLICompleter.get_matches` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::rm` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::describe` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::cd` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::find_executions` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::get_database` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::run_body` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::run_body` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::run_body` c: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::generate_batch_inputs` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx.py::archive` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientRun.setUp` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClient.test_dx_setenv` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClient.test_dx_object_properties` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientWorkflow.test_dx_update_stage` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientUploadDownload.test_dx_download_resume_and_checksum` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientFind.test_dx_find_public_projects` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientOrg.setUp` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXClientNewProject.test_dx_create_new_project_with_bill_to` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXGetAppsAndApplets.assert_app_get_initialized` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxclient.py::TestDXCp.test_multiple_args` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_add_to_applet` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_create_asset` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_create_asset_with_short_imageid` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_create_asset_with_long_imageid` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_create_asset_with_image_digest` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxabs.py::TestDXFile.test_upload_download_large_file_size_dxfile` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx_bash_helpers.py::build_app_with_bash_helpers` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx_bash_helpers.py::build_app_with_bash_helpers` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dx_bash_helpers.py::TestDXBashHelpers.test_deepdirs` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxpy.py::TestDXSearch.test_find_projects` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_dxpy.py::TestDXSearch.test_find_projects` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.test_dataset_class_basic` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.test_dataset_class_basic_1_1` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.test_dataset_class_cohort_resolution` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.common_vizpayloadbuilder_test_helper_method` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/dataset_utilities.py::get_codings` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: blocked — it cannot run here: `validate_cohort_ids` calls `raw_api_call`, which performs a network request via `dxpy.DXHTTPRequest` to the Vizserver (`resp["url"] + "/data/3.0/" + resp["dataset"] + "/raw"`); its work starts with that server request and no input can avoid it.
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.descriptor_file_dict` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_names_list` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/dx_extract_utils/retrieve_bins.py::retrieve_bins` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/dx_extract_utils/filter_to_payload.py::final_payload` a: deferred — accepted in step 2 and its inputs are ready in .energy-inputs/status.json, but no repair was written for it in this run, so nothing was measured
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/dxdatabase.py::DXDatabase.get_download_url` a: blocked — it cannot run here: `DXDatabase.get_download_url` performs its work by calling `dxpy.api.database_download_file(self._dxid, args, **kwargs)`, an HTTP request to the DNAnexus API server; with no network access and no way to stub the API call (no monkeypatching/mocks allowed), the only runnable path is a pure cache hit that does no real work.
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.describe_underlying_workflow` a: blocked — it cannot run here: `describe_underlying_workflow` obtains its result by calling `self.describe()` and `dxpy.DXWorkflow(...).describe()`, which issue authenticated HTTP requests to the DNAnexus platform API; there is no input that avoids this network access.
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/dxfile_functions.py::_download_dxfile` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/bindings/dxfile.py::DXFile._write2` a: blocked — it cannot run here: `DXFile._write2` performs its real work by dispatching remote upload requests — `_ensure_write_bufsize` queries the project's upload parameters from the DNAnexus API server and the write path calls `_async_upload_part_request`/`upload_part` (HTTP part uploads) — so no input can exercise the function (buffering, splitting into parts, uploading) without network access to the DNAnexus API.
- `src/python/dxpy/bindings/dxfile.py::DXFile.__iter__` a: blocked — it cannot run here: `DXFile.__iter__` obtains its data by calling `self.read(...)`, which for a `DXFile` is the remote-file reader that fetches file content from the DNAnexus platform (an API/HTTP download); the class holds no local data source, so no input can make it run without network/service access.
- `src/python/dxpy/cli/download.py::download` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/download.py::download` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — the generator failed: BrokenPipeError: [Errno 32] Broken pipe
- `src/python/dxpy/cli/workflow.py::update_stage` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/resolver.py::resolve_path` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/resolver.py::resolve_job_ref` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/resolver.py::resolve_multiple_existing_paths` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/describe.py::get_resolved_jbors` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/app_builder.py::upload_resources` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` b: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/scripts/dx_build_app.py::build_and_upload_locally` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/file_load_utils.py::get_job_input_filenames` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
- `src/python/dxpy/utils/completer.py::DXAppCompleter._populate_matches` a: deferred — accepted in step 2; no repair was written for it and no inputs were requested for this unit in this run, so nothing was measured
