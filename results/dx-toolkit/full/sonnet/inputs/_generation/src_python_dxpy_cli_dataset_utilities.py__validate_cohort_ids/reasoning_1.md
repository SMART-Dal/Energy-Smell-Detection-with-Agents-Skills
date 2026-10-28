The function `validate_cohort_ids` calls `raw_api_call` which does an HTTP request via `dxpy.DXHTTPRequest`. That's a network call. The task says: a function whose work starts with a request to a server cannot run here.

Can we avoid it? The function calls `raw_api_call(resp, payload)` which calls `dxpy.DXHTTPRequest`. We can't mock. We could set... hmm. Is there a way to make DXHTTPRequest return without network? No, that's faking the environment.

Actually the instruction says: "If the function cannot run here at all -- it needs network access, a remote service... do not write code: reply with one line CANNOT RUN: <the reason>."

This function requires a network request to a Vizserver. So CANNOT RUN.

But wait—could we monkeypatch? No, forbidden. Could we set resp to something that avoids it? raw_api_call always calls DXHTTPRequest. No way around.

So answer: CANNOT RUN.