The function `create_emeritus_prs` calls `fetch_readme(repo)` which does a network request. That's the very first thing in the loop. So it cannot run without network access... unless we can avoid it.

Wait, but the task says "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here". Here, the function calls fetch_readme which does `request_with_retry("GET", url)`. That's network. And later _ensure_fork, _get_default_branch_sha, _update_file, _create_pr all do network.

So this can't run at all. Unless... inactive_report is empty, then the loop body doesn't execute. But that's not a real workload.

Hmm. But the requirement says cases must be real workloads with substantial work. Given the function requires network for every meaningful input, we should reply CANNOT RUN.

Let me double check: `for repo, inactive_list in sorted(inactive_report.items())`. If inactive_report is empty, no network. But then the function does nothing—the timing would be trivial. The instructions say cases must do substantial work. So there's no way to make this run meaningfully.

The answer: CANNOT RUN.

Actually, wait. Let me reconsider. Is there any possibility? The function's core logic (consolidation of roles, README modification) is all interleaved with network calls. fetch_readme is called first for each repo. So any non-empty inactive_report triggers a network request.

So yes, CANNOT RUN.

The instruction says reply with one line `CANNOT RUN: <the reason>`.

I'll do that.