import fnmatch
files = [l.strip() for l in open('/tmp/allpy.txt') if l.strip()]
groups = {
 'G1': ['src/python/dxpy/scripts/dx.py'],
 'G2': ['src/python/test/test_dxclient.py#1-6174'],
 'G3': ['src/python/test/test_dxclient.py#6175-end'],
 'G4': ['src/python/test/test_dxpy.py','src/python/test/test_nextflow.py','src/python/test/test_dx_bash_helpers.py'],
 'G5': ['src/python/test/test_extract_expression.py','src/python/test/test_extract_assay.py','src/python/test/test_create_cohort.py','src/python/test/test_extract_dataset_codings.py','src/python/test/test_extract_somatic.py','src/python/test/test_extract_dataset.py','src/python/test/test_dxfile_download.py','src/python/test/test_dxasset.py','src/python/test/expression_test_assets/*'],
 'G6': ['src/python/dxpy/cli/dataset_utilities.py','src/python/dxpy/api.py','src/python/dxpy/bindings/__init__.py','src/python/dxpy/bindings/search.py'],
 'G7': ['src/python/dxpy/utils/resolver.py','src/python/dxpy/utils/describe.py','src/python/dxpy/app_builder.py','src/python/dxpy/workflow_builder.py','src/python/dxpy/scripts/dx_build_app.py'],
 'G8': ['src/python/dxpy/bindings/dx*.py','src/python/dxpy/bindings/mount_all_inputs.py','src/python/dxpy/bindings/download_all_inputs.py','src/python/dxpy/bindings/auth.py'],
 'G9': ['src/python/dxpy/utils/*.py','src/python/dxpy/__init__.py','src/python/dxpy/exceptions.py','src/python/dxpy/dxlog.py','src/python/dxpy/compat.py','src/python/dxpy/app_categories.py','src/python/dxpy/toolkit_version.py','src/python/dxpy/ssh_tunnel_app_support.py','src/python/dxpy/system_requirements.py','src/python/dxpy/executable_builder.py','src/python/dxpy/asset_builder.py'],
 'G10': ['src/python/dxpy/cli/*.py','src/python/dxpy/scripts/*.py','src/python/dxpy/templating/*.py','src/python/dxpy/templating/templates/*/*/src/*.py','src/python/dxpy/templating/templates/*/*/test/*.py'],
 'G11': ['src/python/dxpy/dx_extract_utils/*.py','src/python/dxpy/bindings/apollo/*.py','src/python/dxpy/bindings/apollo/schemas/*.py'],
 'G12': ['src/python/dxpy/nextflow/*.py','src/python/test/test_nextflow_*.py','src/python/test/dxpy_testutil.py','src/python/test/mock_api/*.py','src/python/test/utils/*.py','src/python/test/nextflow/*.py'],
 'G13': ['*'],  # remainder
}
assigned = {}
out = {}
for g, pats in groups.items():
    if g == 'G13': continue
    for p in pats:
        if '#' in p:
            out.setdefault(g, []).append(p); continue
        m = [f for f in files if fnmatch.fnmatch(f, p) and f not in assigned]
        for f in m: assigned[f] = g
        out.setdefault(g, []).extend(m)
rest = [f for f in files if f not in assigned]
out['G13'] = rest
for g in sorted(out, key=lambda x:int(x[1:])):
    print(g, len(out[g]))
    open(f'/tmp/energy-groups/{g}.txt','w').write('\n'.join(out[g])+'\n')
print('total', sum(len(v) for v in out.values()), 'files', len(files))
