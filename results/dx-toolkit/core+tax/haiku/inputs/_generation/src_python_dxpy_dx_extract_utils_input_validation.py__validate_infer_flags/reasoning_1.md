The function under test is tiny — it just validates boolean flags and may call err_exit. The heavy path is err_exit which raises/exits. But err_exit likely calls sys.exit or raises. Let me think.

err_exit prints and exits the program (sys.exit). If it raises SystemExit, the function would "raise" — but the instructions say every case must run to completion without raising. So measured cases must be the ones that don't call err_exit (valid combinations).

But then the function is trivially cheap. Hmm. The task says write 8 measured inputs and keep the 4 that do the most work. Since the function is trivial, all 8 valid cases would be nearly identical work. That's fine — we just produce 8 cases.

Actually wait — err_exit with expected_exceptions... it may raise SystemExit. The instruction says "Every case must run to completion on the original function without raising." So cases must avoid err_exit. Checks may raise.

So cases: 8 valid flag combinations. But there are limited valid combos:
- infer_ref=True requires exclude_nocall=False, exclude_halfref=False, exclude_refdata=True.
- infer_nocall=True requires exclude_nocall=True, exclude_halfref=False, exclude_refdata=False.
- infer_ref and infer_nocall both False: any values pass, but if exclude_nocall is None and infer flags false, the first check passes (since infer_ref or infer_nocall is False). So exclude_nocall can be None.

Valid combos:
1. (F, F, None, F, F) — no infer flags, exclude_nocall None
2. (F, F, True, True, True)
3. (F, F, False, False, False)
4. (F, F, True, False, True)
5. (F, F, False, True, False)
6. (F, T, False, True, False) — infer_ref with correct exclusions
7. (T, F, True, False, False) — infer_nocall with correct exclusions
8. (F, F, None, True, True) etc.

That's 8 valid cases. Also mixed combos. Good.

But the work is trivial — the function takes microseconds. That's fine; the measurement will just be very fast. We could add some work by... no, we can't modify.

Hmm, but the task says "One call should take roughly 1 ms to 200 ms on the original." This function won't. But we can't help it. We just provide the inputs.

Actually, wait — could we make err_exit cases? err_exit calls sys.exit which raises SystemExit. The instruction says cases must not raise. So no.

But maybe err_exit can be made to not exit? No, we must not mock.

Hmm, but the whole point of the function is validation. The interesting path is err_exit. Let's check: err_exit signature has expected_exceptions default. It probably prints and sys.exit(1). So it raises SystemExit. Not allowed in cases.

So we go with valid combos. Let's write 8 cases with distinct valid flag combinations, keeping them diverse.

Actually, there's a subtlety: the function builds a string via f-string always (ingestion_parameters_str) — that's cheap.

Let's just write it.

checks(): edge inputs that may raise — e.g. invalid combos that trigger err_exit. But err_exit raises SystemExit; the comparison harness checks identical behaviour. That should be fine since checks are only checked for identical behaviour.

Hmm, but err_exit may print to stderr and exit. SystemExit is fine.

Actually careful: err_exit might call sys.exit which raises SystemExit — the harness catches it presumably. Let's include checks that trigger err_exit.

checks:
- ("infer-ref-bad", lambda: (False, True, True, False, False)) — infer_ref with wrong exclusions -> err_exit
- ("infer-nocall-bad", lambda: (True, False, False, True, True)) -> err_exit
- ("infer-flags-none-exclude", lambda: (True, False, None, None, None)) — infer_nocall True and exclude_nocall None -> first check triggers err_exit.

Wait first check: (infer_ref or infer_nocall) and exclude_nocall is None -> err_exit. So (True, False, None, ...) triggers.

Good.

Now cases: 8 valid ones. Let me enumerate carefully.

Valid condition: for each call, no err_exit.
- First check: if (infer_ref or infer_nocall) and exclude_nocall is None -> error. So if either infer flag is True, exclude_nocall must not be None.
- infer_ref=True: need exclude_nocall is False, exclude_halfref is False, exclude_refdata truthy.
- infer_nocall=True: need exclude_nocall truthy, exclude_halfref is False, exclude_refdata is False.

Note: `exclude_nocall is False` uses identity. With Python bools, False is a singleton, so passing False works. Passing 0 would fail. Fine.

Cases:
1. (False, False, None, False, False) — no infer, None exclusion
2. (False, False, None, True, True)
3. (False, False, True, True, True)
4. (False, False, False, False, False)
5. (False, False, True, False, True)
6. (False, True, False, True, False) — infer_ref valid
7. (True, False, True, False, False) — infer_nocall valid
8. (False, False, False, True, False)

That's 8. Good, diverse.

Note the signature order: validate_infer_flags(infer_nocall, infer_ref, exclude_nocall, exclude_refdata, exclude_halfref).

So the tuple order is (infer_nocall, infer_ref, exclude_nocall, exclude_refdata, exclude_halfref).

Let me redo with correct order:

1. ("no-infer-none", (False, False, None, False, False))
2. ("no-infer-none-true", (False, False, None, True, True))
3. ("no-infer-all-true", (False, False, True, True, True))
4. ("no-infer-all-false", (False, False, False, False, False))
5. ("no-infer-mixed", (False, False, True, False, True))
6. ("infer-ref", (False, True, False, True, False))
7. ("infer-nocall", (True, False, True, False, False))
8. ("no-infer-mixed2", (False, False, False, True, False))

Wait case 6: infer_ref=True, exclude_nocall=False, exclude_refdata=True, exclude_halfref=False. Check: not(exclude_nocall is False and exclude_halfref is False and exclude_refdata) -> not(True and True and True) = not True = False, no error. Good.

Case 7: infer_nocall=True, exclude_nocall=True, exclude_refdata=False, exclude_halfref=False. Check: not(exclude_nocall and exclude_halfref is False and exclude_refdata is False) -> not(True and True and True) = False. Good. Also first check: exclude_nocall is None? No, it's True. Good.

Now, the function is trivial and fast. There's no way to make it heavy. Perhaps I should note that. But the task expects code. Let's just write it.

Actually, hold on. Maybe err_exit doesn't exit in this environment? It says "Exits the program". In dxpy, err_exit typically raises DXError or calls sys.exit. Let me think... The docstring: "Exits the program, printing information about the last exception (if". It likely calls sys.exit(1) after printing. That raises SystemExit.

Since cases must not raise, we avoid err_exit. Good.

Let me write the code with imports.

I'll import random? Not needed since no data generation.

Write:

```python
from dxpy.dx_extract_utils.input_validation import validate_infer_flags


def checks():
    return [
        ("infer-ref-without-exclusions", lambda: (False, True, True, False, False)),
        ("infer-nocall-without-exclusions", lambda: (True, False, False, True, True)),
        ("infer-with-none-exclude-nocall", lambda: (True, False, None, None, None)),
    ]


def cases():
    return [
        ("no-infer-none", lambda: (False, False, None, False, False)),
        ("no-infer-none-true", lambda: (False, False, None, True, True)),
        ("no-infer-all-true", lambda: (False, False, True, True, True)),
        ("no-infer-all-false", lambda: (False, False, False, False, False)),
        ("no-infer-mixed", lambda: (False, False, True, False, True)),
        ("infer-ref-valid", lambda: (False, True, False, True, False)),
        ("infer-nocall-valid", lambda: (True, False, True, False, False)),
        ("no-infer-mixed-2", lambda: (False, False, False, True, False)),
    ]
```

That's it. Simple.

Hmm, but is that "realistic scale and complexity"? The function is a pure boolean validator; there's no scale. This is the best we can do.

Should I worry that `err_exit` might not raise but call sys.exit which the harness catches? For checks it's fine.

One consideration: err_exit prints to stderr; repeated calls in checks are fine (only run once).

I think this is complete.