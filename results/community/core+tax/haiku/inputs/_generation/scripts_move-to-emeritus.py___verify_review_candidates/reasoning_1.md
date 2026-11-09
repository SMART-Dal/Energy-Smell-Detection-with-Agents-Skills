The function under test makes HTTP requests via `request_with_retry` to `https://api.github.com`. This requires network access. The task says: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

So this cannot run. Reply with CANNOT RUN.

Wait — but maybe we could set up a local server? No, no network access allowed, and no faking environment. The function calls `urllib.request.urlopen` on a real URL. We can't intercept without monkeypatching.

So the answer is CANNOT RUN.