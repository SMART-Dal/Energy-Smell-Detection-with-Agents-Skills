The issue: `os.chdir(WORKDIR)` may not work because the file reads relative to CWD. Maybe WORKDIR isn't the cwd when the function is called, or chdir happens at import but the test harness changes cwd. Actually the error says it can't find 'dataset/orders.csv' — meaning cwd isn't WORKDIR when the function runs. So chdir at module import doesn't persist.

Better approach: chdir inside the thunk. But chdir in the thunk affects timing? chdir is fast. But we need it to run before the call. Actually thunks run before timing starts, so chdir in thunk is fine.

But wait — the function writes output files, and output_dir is a Path we pass. That's fine, absolute path.

Let me just chdir in each thunk. Actually simpler: chdir at module level AND in the thunk. Let me put chdir in the thunk.

Actually, the problem may be that the harness runs from a different cwd. Let me make the thunk do `os.chdir(WORKDIR)` before returning args.

Let me rewrite.

Also `limit-zero`: limit=0, `if not full and i >= limit - 1` → i >= -1 always true, so breaks after first write. Fine.

Let me put os.chdir(WORKDIR) in each thunk.