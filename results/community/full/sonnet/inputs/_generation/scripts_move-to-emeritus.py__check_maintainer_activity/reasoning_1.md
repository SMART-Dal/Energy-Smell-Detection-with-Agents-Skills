The function under test makes network calls (request_with_retry to GitHub GraphQL API, and _check_comments uses _get_repo_commenters which presumably does REST calls). This requires network access. So we cannot run it.

Indeed, the function's work starts with a request to a server. We must reply CANNOT RUN.