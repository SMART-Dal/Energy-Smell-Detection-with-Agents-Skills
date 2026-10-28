# Energy report — dx-toolkit @ accd86a

177 units listed, 57 with an accepted suspicion · 7 repairs submitted, 30 deferred · 2 confirmed · 3 negligible · 2 no_inputs · 2 applied
Noise floor 1.2% (from: session calibration).

## Applied

### `src/python/dxpy/dxlog.py::DXLogHandler.truncate_message` — dxlog-truncate-bisect

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| control-20k | 102.45 | 0.14 | +99.9% | 0.1% | yes |
| two-byte-20k | 102.93 | 0.30 | +99.7% | 0.1% | yes |
| four-byte-20k | 104.26 | 0.41 | +99.6% | 0.0% | yes |
| mixed-30k | 96.01 | 0.41 | +99.6% | 0.0% | yes |

### `src/python/dxpy/__init__.py::_get_pool_manager` — pool-manager-cache

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +37.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| verify-false | 50.72 | 42.15 | +16.9% | 8.3% | yes |
| dx-ca-noverify | 49.49 | 41.26 | +16.6% | 3.8% | yes |
| proxy-auth | 89.00 | 36.20 | +59.3% | 0.4% | yes |
| proxy-noauth | 90.20 | 39.07 | +56.7% | 0.4% | yes |

## Measured, not confirmed

### `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe` — coding-display-position-dict

**negligible** — no case moved more than the noise: the largest reading was -1.5% +-8.2% on 'hier-no-concepts', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hier-large | 72.49 | 71.46 | +1.4% | 5.5% | no: pairs disagree |
| hier-wide | 73.65 | 73.10 | +0.7% | 1.9% | no: pairs disagree |
| hier-paginated | 71.19 | 70.95 | +0.3% | 0.6% | no: pairs disagree |
| hier-no-concepts | 73.07 | 74.16 | -1.5% | 8.2% | no: pairs disagree |

### `src/python/dxpy/bindings/search.py::_find` — find-stop-at-limit

**negligible** — no case moved more than the noise: the largest reading was -1.7% +-3.5% on 'capped-limit', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.5%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-pages | 54.87 | 54.61 | +0.5% | 3.0% | no: pairs disagree |
| capped-limit | 54.40 | 55.31 | -1.7% | 3.5% | no: pairs disagree |
| kwarg-project | 55.52 | 55.78 | -0.5% | 3.2% | no: pairs disagree |
| big-pages | 55.13 | 55.37 | -0.4% | 1.0% | no: pairs disagree |

### `src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on` — depends-on-no-discarded-describe

**negligible** — no case moved more than the noise: the largest reading was -0.8% +-1.6% on 'medium', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.2%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| medium | 57.94 | 58.38 | -0.8% | 1.6% | no: pairs disagree |
| large | 57.22 | 57.50 | -0.5% | 1.8% | no: pairs disagree |
| huge | 57.74 | 57.90 | -0.3% | 0.8% | no: pairs disagree |
| dense-medium-dict | 57.20 | 56.82 | +0.7% | 2.1% | no: pairs disagree |

## Not measured

### `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` — validate-ids-comprehension

**no_inputs** — no inputs could be generated for src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids: it cannot run here: `validate_cohort_ids` sends a POST request to a Vizserver via `raw_api_call`, which calls `dxpy.DXHTTPRequest` (network access), and no input can avoid that. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `src/python/dxpy/cli/output_handling.py::write_expression_output` — output-colset-once

**no_inputs** — no inputs could be generated for src/python/dxpy/cli/output_handling.py::write_expression_output: the generator failed: BrokenPipeError: [Errno 32] Broken pipe. Next: the unit has had its 3 tries; its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `src/python/dxpy/app_builder.py::upload_resources` a: blocked — generator: it cannot run here: `upload_resources` requires network access to the DNAnexus platform for any non-empty resources directory — it either calls `dxpy.find_one_data_object` (to look for an existing bundle) or `dxpy.upload_local_file` (to upload the new tarball). The only input that avoids the network is an empty/missing resources directory, which returns `[]` without doing the function's real work, so no meaningful measured workload can run here.
- `src/python/dxpy/app_builder.py::upload_resources` b: blocked — generator: it cannot run here: `upload_resources` requires network access to the DNAnexus platform for any non-empty resources directory — it either calls `dxpy.find_one_data_object` (to look for an existing bundle) or `dxpy.upload_local_file` (to upload the new tarball). The only input that avoids the network is an empty/missing resources directory, which returns `[]` without doing the function's real work, so no meaningful measured workload can run here.
- `src/python/dxpy/asset_builder.py::build_asset` a: blocked — generator: it cannot run here: `build_asset` requires the DNAnexus platform — it calls `dxpy.api.system_whoami()`, uploads files via `dxpy.upload_local_file`, and runs jobs with `dxpy.api.app_run`/`dxpy.api.job_describe` over the network with credentials, which cannot be avoided by any input.
- `src/python/dxpy/workflow_builder.py::_assert_executable_regions_match` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/ssh_tunnel_app_support.py::get_notebook_app_versions` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/ssh_tunnel_app_support.py::poll_for_server_running` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/nextflow/collect_images.py::_populate_cached_file_ids` a: blocked — generator: it cannot run here: the function's real work is entirely `find_data_objects(...)`, which calls the DNAnexus platform API (`system_find_data_objects`) over the network and needs credentials; with no `DX_PROJECT_CONTEXT_ID` it returns immediately without doing any work, and the lookup path cannot be exercised without mocking that call.
- `src/python/dxpy/nextflow/nextflow_builder.py::build_pipeline_with_npi` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/scripts/dx_build_app.py::_build_app_remote` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/scripts/dx_build_app.py::build_and_upload_locally` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` a: blocked — generator: it cannot run here: `_check_suggestions` performs DNAnexus API requests (`dxpy.api.project_describe` and `dxpy.describe`) for the suggestions it examines in the real `dxapp.json` inputs the repository passes it; these require network access and credentials, and their failure (a connection error, not a caught 404 `DXAPIError`) propagates out of the function. No input that exercises the function's actual work can avoid those server calls, and they cannot be stubbed without mocking the repository's
- `src/python/dxpy/scripts/dx_build_app.py::_check_suggestions` c: blocked — generator: it cannot run here: `_check_suggestions` performs DNAnexus API requests (`dxpy.api.project_describe` and `dxpy.describe`) for the suggestions it examines in the real `dxapp.json` inputs the repository passes it; these require network access and credentials, and their failure (a connection error, not a caught 404 `DXAPIError`) propagates out of the function. No input that exercises the function's actual work can avoid those server calls, and they cannot be stubbed without mocking the repository's
- `src/python/dxpy/scripts/dx.py::get_database` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/scripts/dx.py::run_body` b: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/scripts/dx.py::ssh` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/dx_extract_utils/retrieve_bins.py::retrieve_bins` a: blocked — generator: it cannot run here: the function begins with `dxpy.describe(project)` and later `dxpy.describe(...)` and `subprocess.check_output(["dx", "cat", ...])`, all of which require network access to the DNAnexus platform and the `dx` CLI (subprocesses are not permitted), so no input can avoid it.
- `src/python/dxpy/bindings/dxdatabase_functions.py::_download_dxdatabasefile` a: blocked — generator: it cannot run here: `_download_dxdatabasefile` must reach the DNAnexus platform: it calls `dxdatabase.get_download_url(...)` (an API request for a download URL) and `dxpy._dxhttp_read_range(url, headers, start, end, ...)` (an HTTP range request to fetch the file bytes), so every call requires network access and credentials that cannot be provided here.
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assays_info_dict` a: blocked — generator: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: RecursionError: maximum recursion depth exceeded in comparison)
- `src/python/dxpy/bindings/apollo/dataset.py::Dataset.assay_names_list` a: blocked — generator: the generated inputs could not be used: the source does not load (cases): DXError: Invalid ID of class record: 'dataset-0000' (at line 51 of your source: `ds = Dataset("dataset-0000", detail)`)
- `src/python/dxpy/bindings/download_all_inputs.py::_gen_helper_dict` a: deferred — accepted in step 2 but not repaired: on re-check the repair must reproduce the path, basename and prefix that analyze_bash_vars takes from the job input file and from a platform describe per file, and the inputs passed here carry only the names, so dropping the call cannot be made to behave identically from the argument alone
- `src/python/dxpy/bindings/mount_all_inputs.py::_gen_helper_dict` a: deferred — not requested for inputs in this session; same shared shape as download_all_inputs._gen_helper_dict, where the repair cannot be made to behave identically from the argument alone
- `src/python/dxpy/bindings/dxfile.py::DXFile.__iter__` a: blocked — generator: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: ResourceNotFound: The entity file-000000000000000000000000 could not be found, code 404. Request Time=1793148343.9033177, Request ID=1793148344072-987509)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow.get_underlying_workflow` a: blocked — generator: only 0 of 8 generated inputs ran and repeated on the original code (most often: building or running it failed: RecursionError: maximum recursion depth exceeded in comparison)
- `src/python/dxpy/bindings/dxglobalworkflow.py::DXGlobalWorkflow._get_run_input` a: blocked — generator: it cannot run here: `DXGlobalWorkflow._get_run_input` begins with `dxpy.api.project_describe(project, ...)`, a live DNAnexus API call to the platform, and then calls `get_underlying_workflow(region)`, which also resolves/describes remote workflows; no input can avoid these network requests.
- `src/python/dxpy/bindings/dxjob.py::DXJob.wait_on_done` a: blocked — generator: it cannot run here: `DXJob.wait_on_done` polls a remote DNAnexus job by calling `self._get_state(...)` (i.e. `self.describe(io=False)["state"]`) in a loop, which performs an API request to the DNAnexus server and needs network access plus credentials; the only non-raising path requires the server to report a state, and nothing in the task documents a way to supply that state locally, so no input can make this function run here.
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` a: blocked — generator: it cannot run here: `extract_assay_expression` starts by resolving the `--path` argument through `resolve_existing_path`, then builds `DXRecord`/`Dataset` objects and reads dataset descriptors and assay info from the DNAnexus platform API, all of which require network access and credentials that are unavailable here.
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` b: blocked — generator: it cannot run here: `extract_assay_expression` starts by resolving the `--path` argument through `resolve_existing_path`, then builds `DXRecord`/`Dataset` objects and reads dataset descriptors and assay info from the DNAnexus platform API, all of which require network access and credentials that are unavailable here.
- `src/python/dxpy/cli/dataset_utilities.py::extract_assay_expression` c: blocked — generator: it cannot run here: `extract_assay_expression` starts by resolving the `--path` argument through `resolve_existing_path`, then builds `DXRecord`/`Dataset` objects and reads dataset descriptors and assay info from the DNAnexus platform API, all of which require network access and credentials that are unavailable here.
- `src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids` a: blocked — verify.py: no_inputs. it cannot run here: `validate_cohort_ids` sends a POST request to a Vizserver via `raw_api_call`, which calls `dxpy.DXHTTPRequest` (network access), and no input can avoid that.
- `src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.load_data_dictionary` a: blocked — generator: only 0 of 8 generated inputs ran and repeated on the original code (most often: the original raises TypeError: list indices must be integers or slices, not dict)
- `src/python/dxpy/cli/dataset_utilities.py::get_codings` a: blocked — generator: it cannot run here: `get_codings` does its work by issuing an HTTP request to the DNAnexus API server through `dxpy.DXHTTPRequest` (via `viz_meta_codings_page`), so it needs network access and credentials; the only way to give it inputs here would be to replace that request with canned responses, which the rules forbid (no mocks/monkeypatching, no fake servers).
- `src/python/dxpy/cli/output_handling.py::write_expression_output` a: blocked — verify.py: no_inputs. the generator failed: BrokenPipeError: [Errno 32] Broken pipe, on all three tries
- `src/python/dxpy/cli/exec_io.py::ExecutableInputs.update_from_args` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/cli/workflow.py::update_stage` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/cli/download.py::download` a: blocked — generator: it cannot run here: `download()` resolves every path through `resolve_existing_path` and then calls the DNAnexus platform API (`dxpy.list_subfolders`, `object_exists_in_project`, `dxpy.download_folder`, and `download_one_file`'s object download), all of which require network access and credentials; no realistic input can avoid these server requests.
- `src/python/dxpy/utils/describe.py::get_resolved_jbors` a: blocked — generator: the inputs that run here reach only 36% of the function (lines 291, 293-303, 305, 309 never ran), so they would not measure its real work
- `src/python/dxpy/utils/completer.py::path_completer` b: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/dxpy/utils/batch_utils.py::batch_run` a: blocked — generator: it cannot run here: `batch_run` calls `executable.describe()` and `executable.run(...)`, which are DNAnexus API requests to a remote server (requiring network access and credentials); a stand-in executable returning canned results would be a mock, which is not allowed.
- `src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on` b: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dxclient.py::TestDXClientRun.test_dx_describe_job_with_resolved_jbors` a: blocked — generator: it cannot run here: the test creates applets and runs jobs on the DNAnexus platform (dxpy.api.applet_new, dxpy.api.applet_run, job.wait_on_done, `dx describe`), requiring network access, valid credentials and a live remote project that are unavailable here.
- `src/python/test/test_dxclient.py::TestDXClient.test_dx_run_debug_on` a: blocked — generator: it cannot run here: the test creates applets and jobs on the DNAnexus platform (`dxpy.api.applet_new`, `dx run`, `dxpy.describe`) and opens an SSH session to a running job with pexpect, all of which require network access to a remote server and real platform credentials.
- `src/python/test/test_dxpy.py::TestDXSearch.test_resolve_data_objects` a: blocked — generator: it cannot run here: `TestDXSearch.test_resolve_data_objects` drives the live DNAnexus platform — it calls `testutil.temporary_project` and `dxpy.new_dxrecord` to create projects/records on a server, and `dxpy.search.resolve_data_objects` performs classify/describe API calls against it. No input can avoid these network/credentialed service requests.
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.common_vizpayloadbuilder_test_helper_method` b: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_extract_expression.py::TestDXExtractExpression.common_vizpayloadbuilder_test_helper_method` c: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_extract_dataset.py::TestDXExtractDataset.end_to_end_ddd` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_extract_dataset.py::TestDXExtractDataset.end_to_end_fields` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/dxpy_testutil.py::analysis_describe_with_retry` a: blocked — generator: it cannot run here: the function's entire work is polling a DNAnexus API object's `describe()` (a remote server request) — whether given an analysis ID (via `dxpy.get_handler`) or a handler, and no input avoids that network access; faking a handler with canned `describe()` output would be a mock, which is not allowed.
- `src/python/test/dxpy_testutil.py::DXTestCaseBuildWorkflows.setUp` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_create_cohort.py::TestCreateCohort.test_raw_cohort_query_api` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_create_cohort.py::TestCreateCohort.test_create_pheno_filter` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dx_bash_helpers.py::build_app_with_bash_helpers` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_add_to_applet` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dx-docker.py::TestDXDocker.test_dx_docker_create_asset` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dx_bash_helpers.py::TestDXBashHelpers.test_deepdirs` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_dxasset.py::TestDXBuildAsset.test_build_asset_with_valid_dxasset` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_nextflow.py::TestNextflowOfflineMode::test_quoted_offline_tokens` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_nextflow.py::TestNextflowOfflineMode::test_opt_out_also_drops_bare_offline` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
- `src/python/test/test_nextflow.py::TestNextflowOfflineMode::test_setup_offline_mode_fails_open` a: deferred — accepted in step 2 and not requested for inputs in this session, so not measured
