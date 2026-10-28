```python
from dxpy.dx_extract_utils.input_validation import validate_infer_flags


def checks():
    # Small edge inputs, checked only for identical behaviour (these hit the
    # err_exit validation branches and may raise).
    return [
        # infer_ref set but ingestion exclusions are wrong -> err_exit
        ("infer-ref-without-exclusions", lambda: (False, True, True, False, False)),
        # infer_nocall set but ingestion exclusions are wrong -> err_exit
        ("infer-nocall-without-exclusions", lambda: (True, False, False, True, True)),
        # infer flag set while exclude_nocall is None -> err_exit
        ("infer-with-none-exclude-nocall", lambda: (True, False, None, None, None)),
    ]


def cases():
    # validate_infer_flags(infer_nocall, infer_ref, exclude_nocall, exclude_refdata, exclude_halfref)
    # Only valid (non-exiting) flag combinations can be measured, since every
    # measured case must run to completion.  We cover the distinct valid paths.
    return [
        # no infer flags, unknown ingestion exclusions
        ("no-infer-none", lambda: (False, False, None, False, False)),
        ("no-infer-none-true", lambda: (False, False, None, True, True)),
        # no infer flags, all exclusions on
        ("no-infer-all-true", lambda: (False, False, True, True, True)),
        # no infer flags, all exclusions off
        ("no-infer-all-false", lambda: (False, False, False, False, False)),
        # no infer flags, mixed exclusions
        ("no-infer-mixed", lambda: (False, False, True, False, True)),
        ("no-infer-mixed-2", lambda: (False, False, False, True, False)),
        # infer_ref with the matching ingestion exclusions
        ("infer-ref-valid", lambda: (False, True, False, True, False)),
        # infer_nocall with the matching ingestion exclusions
        ("infer-nocall-valid", lambda: (True, False, True, False, False)),
    ]
```