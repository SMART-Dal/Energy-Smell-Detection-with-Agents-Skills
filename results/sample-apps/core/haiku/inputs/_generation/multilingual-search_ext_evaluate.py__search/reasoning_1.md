The function `search` makes an HTTP POST to `args.endpoint`. That starts with a request to a server. Per the instructions: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

The function's work begins with `session.post(...)`. We cannot do network access. Could we avoid it? No — the post is essential and the endpoint is a real remote service. There's no way to make it run without network.

So reply with CANNOT RUN.

Wait — could we run a local HTTP server? "No network access, no subprocesses." Setting up a local server would require a subprocess or threads... Actually we could use a thread with http.server. But the instructions say no network access, and faking the environment is not allowed. Hmm, but a local server is real network... The rule says "no network access, no subprocesses". A local in-process HTTP server would be network access (localhost). I think the intent is clearly: this cannot run.

Also the function requires `args`, `session`, `responses` globals which are set by main() from command line. We could set them, but the post is the blocker.

Reply one line.