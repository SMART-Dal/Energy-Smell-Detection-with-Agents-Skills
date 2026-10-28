The function under test `_check_reviews` makes network calls (GraphQL API, REST API). It cannot run here at all — it starts with `request_with_retry` to `GRAPHQL_API` (a remote service). No input could avoid that.

So reply with one line `CANNOT RUN: ...`.

Wait, but the instructions say a function whose work starts with a request to a server cannot run here. This is clearly the case. So CANNOT RUN.