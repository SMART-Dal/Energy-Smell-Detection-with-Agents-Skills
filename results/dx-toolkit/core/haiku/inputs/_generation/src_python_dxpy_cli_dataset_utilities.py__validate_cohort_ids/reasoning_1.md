The function `validate_cohort_ids` calls `raw_api_call(resp, payload)` which calls `dxpy.DXHTTPRequest` - a network request. This cannot run here.

Wait, let me re-read. The function's work starts with a request to a server. The instructions say: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

`raw_api_call` calls `dxpy.DXHTTPRequest(resource=resource_val, data=payload, prepend_srv=False)`. This is a network call. So this function cannot run here.

So the answer is `CANNOT RUN: ...`.

Let me verify - the function under test does a POST request to a Vizserver via dxpy.DXHTTPRequest. Yes, network access required.

So reply with one line.