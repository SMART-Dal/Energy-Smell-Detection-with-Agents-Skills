```python
CANNOT RUN: _check_reviews performs live GitHub API calls (request_with_retry -> urllib.request.urlopen against GRAPHQL_API / REST_API) for every non-empty input, so no realistic input can run without network access.
```