The issue: the file path changes between runs (because of the counter), so the "files it wrote" differ by name. The harness apparently compares the set of files written. I need deterministic file paths. But the function errors if the file exists. So I need to remove the file in the thunk, and use a fixed path.

But the thunk runs before timing, so removing the file there is fine. The problem: the file gets written during the call, then next call needs it removed again. Thunk removes it each time. Good.

So use fixed paths per case, and unlink in the thunk.

Let me rewrite `_fresh` to take a fixed name and unlink it.

Also the "output" comparison might include the file content — deterministic paths fix that.

Let me define:
```python
def _path(name):
    p = WORKDIR / (name + ".out")
    if p.exists():
        p.unlink()
    return str(p)
```

Each case uses its own distinct name. Good.

Now the checks: empty-rows, single-row, sql-stdout. Those are fine.

Let me rewrite.