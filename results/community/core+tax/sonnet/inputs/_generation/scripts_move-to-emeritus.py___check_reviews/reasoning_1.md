The function under test makes network requests. It calls `request_with_retry` which does urllib.request.urlopen. That's network access — cannot run here.

Wait, but maybe we could monkeypatch... no, instructions say no monkeypatching, no network access. The function's work starts with a request to a server. So `CANNOT RUN`.

The task explicitly says: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

`_check_reviews` calls `request_with_retry("POST", GRAPHQL_API, ...)` — network. So CANNOT RUN.

But wait — `if not remaining: return {}`. With empty remaining, no network. But that would be a trivial case, and cases() must do real work. The measured cases need substantial work which requires network. So CANNOT RUN.