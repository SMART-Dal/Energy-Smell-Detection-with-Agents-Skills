Let me analyze the function under test.

`validate_cohort_ids(descriptor, project, resp, ids)`:
- Reads `descriptor.model["global_primary_key"]["entity"]` and `["field"]`
- Gets `gpk_type` from `descriptor.model["entities"][entity_name]["fields"][field_name]["mapping"]["column_sql_type"]`
- Converts ids via `reduce` with lambda based on type
- Builds payload
- Calls `raw_api_call(resp, payload)` which calls `dxpy.DXHTTPRequest(...)` — network call!

Wait, `raw_api_call` calls `dxpy.DXHTTPRequest`, which makes an HTTP request. That requires network access. Hmm.

But `raw_api_call` is a function in the module that we could... no, we can't monkeypatch. But the instructions say the function under test calls `raw_api_call`. `raw_api_call` calls `dxpy.DXHTTPRequest`. That's a network call.

Hmm. But wait — the task says we shouldn't mock. But the function's work starts with a request to a server. "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here, even if the rest of it only processes the answer."

Hmm, but `raw_api_call` is part of the repository, not the function under test directly. But it does make a network call.

Wait, but maybe there's a way. Let me reconsider. The instruction says "no network access". `dxpy.DXHTTPRequest` would attempt to make an actual HTTP request. This would fail without network.

Actually, could we set up the environment so DXHTTPRequest works? No, it needs a real server.

Hmm, but the task says "do not try to recall its code from memory". Let me think about whether this can run.

Actually, hold on. Let me reconsider. The task is from a benchmark where they measure energy. Perhaps they expect us to make the function work. But the function calls `raw_api_call` which calls `dxpy.DXHTTPRequest`. Without network this raises an exception, which would be caught... Actually in `validate_cohort_ids`:

```python
try:
    resp_raw = raw_api_call(resp, payload)
except Exception as exc:
    raise VizserverError(...)
```

But `raw_api_call` itself catches exceptions and calls `err_exit(str(details))`. `err_exit` prints and exits the program (sys.exit). So the whole process would exit.

Hmm, that's problematic. Actually `err_exit` with default `code=None`... let me think. It raises SystemExit probably.

So this function cannot run without network. The answer might be `CANNOT RUN`.

But wait — maybe the benchmark environment provides a way. Let me reconsider. Actually maybe `dxpy.DXHTTPRequest` can be pointed to a local server? No, no subprocesses allowed, no fake servers.

Hmm, but actually maybe the benchmark harness sets up something. Let me re-read: "If the function cannot run here at all -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`."

So `validate_cohort_ids` needs network access via `raw_api_call`. That seems like a clear CANNOT RUN.

But wait, is there any way to avoid the network call? The function unconditionally calls `raw_api_call(resp, payload)`. There's no branch that avoids it. So no input could avoid it.

Hmm, but let me think again. Maybe the benchmark harness patches `dxpy.DXHTTPRequest`? The instructions say "no mocks, no monkeypatching". But the harness might set up a fake. Actually no.

Hmm, but actually, wait. Let me reconsider whether `raw_api_call` is really the one used. Yes, `resp_raw = raw_api_call(resp, payload)`.

`raw_api_call` calls `dxpy.DXHTTPRequest(resource=resource_val, data=payload, prepend_srv=False)`. This is an actual HTTP request.

So without network, this fails. Unless... the harness intercepts.

Hmm, this is a tough call. Let me think about what the benchmark intends. The benchmark seems to be about measuring energy of real functions. Many functions in dx-toolkit make network calls. The task explicitly gives the rule: functions whose work starts with a request to a server cannot run.

But this function's work doesn't *start* with a request — it does some processing first (reduce, building payload), then makes a request. Actually the request is a big part of the work. But most of the "work" is the request.

Hmm, actually the rule says "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here, even if the rest of it only processes the answer." The intent is: if the function makes a network request, it can't run.

I think the answer is CANNOT RUN.

But wait, let me reconsider. Maybe there's a way to make `dxpy.DXHTTPRequest` work offline. Actually, dxpy might have a test mode... Hmm, I shouldn't recall.

Actually, let me reconsider the whole thing. The benchmark might have a mechanism where they run in an environment that has these things available. But the instructions clearly say no network access.

Hmm, but actually — maybe the harness replaces `dxpy.DXHTTPRequest`? No, we're told not to mock.

Let me reconsider: The task says "Import the repository's modules exactly as shown in the task." And "no network access". If the function requires network, we say CANNOT RUN.

Given the strong signal, I'll go with CANNOT RUN.

Wait, but let me double check: is there any chance `raw_api_call` is overridable in a legitimate way? The function calls the module-global `raw_api_call`. We could set `dataset_utilities.raw_api_call = ...` — but that's monkeypatching/assigning a function to an attribute, which is explicitly forbidden ("no assigning functions or lambdas to attributes").

So no.

Therefore: CANNOT RUN.

Hmm, but let me reconsider once more. The problem statement is elaborate and gives lots of detail about the function. Usually when a task is CANNOT RUN, it's obvious. Here it's a network call. The detail given might be a distractor, or the benchmark might expect us to realize it's a network function.

Actually, I realize there might be subtlety: `raw_api_call` catches exceptions from `DXHTTPRequest` and calls `err_exit`. `err_exit` raises... Actually if it raises SystemExit, the process dies. Either way, the function doesn't complete normally.

But the requirement for cases is "Every case must run to completion on the original function without raising." We can't satisfy that without network.

So CANNOT RUN it is.

Let me write the reason: it makes an HTTP request to the vizserver via `raw_api_call`/`dxpy.DXHTTPRequest`, requiring network access.

Actually, hold on. Let me reconsider whether the benchmark might have a local vizserver mock. The instructions explicitly forbid network access and fake servers. And "A function whose work starts with a request to a server ... cannot run here."

Final answer: CANNOT RUN.

But wait, I want to be careful. Let me re-read the exact rule once more: "If the function cannot run here at all -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`."

Yes. `validate_cohort_ids` needs network access (POST to vizserver). No input can avoid it. CANNOT RUN.

I'll provide the one-line answer.

Hmm, but the output format says "Exactly one ```python block holding the complete source." But the CANNOT RUN instruction says "reply with one line `CANNOT RUN: <the reason>`". The CANNOT RUN takes precedence.

I'll reply with just that line.