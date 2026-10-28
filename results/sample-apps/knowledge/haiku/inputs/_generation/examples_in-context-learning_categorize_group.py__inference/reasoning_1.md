The function under test makes an HTTP POST to localhost:8080. That's network access. Per the instructions, "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here."

So we should reply with CANNOT RUN.

Let me double-check: `requests.post(f"http://localhost:8080/search/", json=query_request)` - this requires a Vespa server. No network access allowed. So CANNOT RUN.

Reply with one line.