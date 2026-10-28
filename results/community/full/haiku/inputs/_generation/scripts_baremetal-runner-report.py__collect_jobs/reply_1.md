```python
CANNOT RUN: collect_jobs fetches every workflow run and job through gh_paginated, which shells out to `gh api --paginate` against the GitHub API — it needs network access and the gh CLI, and that request is the first thing the function does for each workflow.
```