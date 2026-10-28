The function under test makes network requests (GraphQL API, REST API). It calls `request_with_retry` which uses urllib to hit GitHub. This cannot run here without network access.

The task says: "A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer."

`_check_reviews` starts its work with a GraphQL request. So it cannot run here. Reply with CANNOT RUN.

Wait, but can we mock? No, mocking is forbidden. The function needs network access. So CANNOT RUN.