The function under test calls `get_indexed_docids` which calls `vespa_visit` which makes HTTP requests. Also `vespa_remove` makes HTTP requests, and `vespa_feed` runs a subprocess `vespa`. Network access and subprocesses are forbidden. Can we avoid?

Let's look: `update_endpoint` always calls `get_indexed_docids(endpoint_url, namespace, doc_type)` which calls `vespa_visit` -> network request. So it cannot run here.

Unless... `vespa_visit` uses requests. No way to avoid without mocking. So CANNOT RUN.

Indeed the function's work starts with a request to a server. So reply with one line.

The instructions say: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here". So CANNOT RUN.