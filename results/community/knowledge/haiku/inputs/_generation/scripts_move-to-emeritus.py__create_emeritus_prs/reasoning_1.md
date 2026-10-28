The function `create_emeritus_prs` calls `fetch_readme` which makes network requests. This cannot run here. The function's work starts with a request to a server (fetch_readme → request_with_retry → urllib.request.urlopen). So CANNOT RUN.

The instructions explicitly say: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

So answer with CANNOT RUN.