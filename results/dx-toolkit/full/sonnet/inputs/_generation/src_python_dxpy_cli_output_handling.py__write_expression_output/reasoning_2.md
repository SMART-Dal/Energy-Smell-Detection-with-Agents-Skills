The issue: the file path differs between runs (expr_out_0 vs expr_out_20454). The comparison includes the file path as a key. I need to use a fixed file name so the path is identical across runs. But the function errors if the file already exists. So the thunk must remove the file first, then return the fixed path.

Let me use a fixed path per case, and have the thunk delete it before returning.

Actually the problem is the output includes the written files keyed by path. If path varies, it differs. Use fixed paths.

But multiple cases writing to same path? Each case has its own path. And the thunk must remove the file first (since function errors if exists). Let me do that.

Let me define fixed paths per case and remove in thunk.