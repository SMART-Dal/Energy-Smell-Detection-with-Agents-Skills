The function makes HTTP requests via `request_with_retry`. This needs network access. Per the rules: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here."

The function calls `request_with_retry("GET", reviews_url)` which does `urllib.request.urlopen`. That's network access. We cannot fake the environment (no stand-in programs on PATH, no fake system files). We can't monkeypatch.

So we must reply CANNOT RUN.

Wait — could we set up a local HTTP server? "No network access, no subprocesses." A local server would be... hmm, it says no network access. And we can't monkeypatch urllib. The URL is hardcoded to https://api.github.com.

So CANNOT RUN.