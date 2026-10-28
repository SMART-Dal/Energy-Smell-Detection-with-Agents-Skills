```python
CANNOT RUN: collect_jobs performs all of its work through gh_paginated, which shells out to the `gh api` command to fetch workflow runs and jobs from GitHub; it needs network access and a working `gh` binary, and no input can avoid that (with an empty WORKFLOWS the function would do nothing at all).
```