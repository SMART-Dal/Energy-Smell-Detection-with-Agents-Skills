```python
CANNOT RUN: check_approver_activity performs live GitHub API requests (via _get_repo_commenters -> request_with_retry and the GraphQL search in _check_reviews) to api.github.com; no non-trivial input can avoid network access, and mocking the requests is not allowed.
```