We need to write inputs for `load_msmarco_queries(qrel)` in `text-search/python/extract-msmarco.py`. It reads a gzip TSV file at `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")` where `download_dir = os.path.join("ext", "download")`. It uses module global `download_dir`. Note that `download_dir` is a relative path "ext/download". We need files under WORKDIR. We should set the module's `download_dir` to a path under WORKDIR (e.g., str(WORKDIR / "ext" / "download")). That's the "module globals the function reads must be set on the repository's own module".

The file: gzip-compressed TSV with lines "queryid\tquery". The function reads all lines, substitutes non-word chars with space and lowercases, stores in dict keyed by queryid.

Note the arg `qrel` is unused by the function? Indeed the function signature `load_msmarco_queries(qrel)` but it never uses qrel in the shown code. So qrel can be anything, e.g., {} or a dict. The measured work is reading/filtering the file. Since qrel unused, we can vary its size but it doesn't affect work. Still, we should pass realistic qrel (a dict of queryid->relevance). But its size affects only argument rendering (the arguments are rendered before/after each call to see whether it changed them) — that could be expensive if huge, but under 1M values. Real qrels file for MS MARCO doctrain has ~ 397k lines. But we don't need to make qrel huge; we could make it a realistic dict but it's not used. However, the "same work on every call" requirement: the function doesn't modify qrel, so fine. But the argument rendering includes qrel; keep it moderate.

The real workload: the file `msmarco-doctrain-queries.tsv.gz` real size? MS MARCO doctrain queries has 367,013 lines? Actually MS MARCO passage ranking has 808,731 queries in train. For document ranking maybe 367k queries. The file is around 8 MB gz? Let's check: MS MARCO doc train queries: 367,013 queries. That's a realistic workload. But one call takes how long? Reading gzip 367k lines, regex sub, lowercasing, storing dict. Probably ~0.3-0.5 s in Python? Could be under 1 s maybe. We must avoid over 1s. Let's estimate: regex sub per line on short query strings. 367k lines, each maybe 30 chars. `re.sub(r"[^\w ]", " ", query)` compiled regex is cached internally. Might be ~0.2-0.4s. That's within 1ms-200ms? Actually 0.3s exceeds 200ms but under 1s is allowed? The instructions: "One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped." Hmm, it says should be 1ms-200ms, but allows up to 1s? Contradictory: "roughly 1 ms to 200 ms" then "over 1 s are dropped". I'd aim for 50-200ms. So we need to size the file so that one call takes maybe 100-200ms. Use maybe 100k lines? Let's estimate: maybe 200k lines ~ 0.15s? We can create 8 cases with different sizes and content complexity, but each case should be substantial and different.

But wait: the function reads a fixed file path. We cannot vary the file per thunk call unless we change `download_dir` or rewrite the file each thunk. The thunk returns arguments; the function reads `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")` at call time. Since download_dir is a module global, we could set it per case? But we must ensure each measured call gets its own input. Options:

- Create multiple gzip files in different directories, and set `extract_msmarco.download_dir` to that directory. But the module global is read at call time, so if we set it once and don't change, all cases use the same file. To have different inputs per case, each thunk could set the module global before returning argument? But thunks run before timing starts; however, setting a global in the thunk... The thunk is run before the timing of the call, so yes we could have the thunk set `extract_msmarco.download_dir = str(path_for_case)`. But wait: is that allowed? "Setup is never timed: everything that builds data, objects or files goes in the thunk or in module-level code." Setting a module global is setup. But careful: "Module globals the function reads must be set on the repository's own module". So yes, in the thunk we can do `mod.download_dir = ...` and return `(qrel,)`. That would make each case use a different file.

However, there's a subtlety: the file must exist under WORKDIR at call time. We can create 8 different gzip files at module level (or in thunks). That's fine. But building 8 files each with ~100k lines could take time (compression) but under 10s. Could also rewrite the same file before each case? But cases are run in sequence; each case's thunk runs before its own timed call (maybe all thunks run first? The harness: "Thunks run before the timing starts; only the call of the function is timed." For each input many times in a row? Actually we run them on original and modified, each input many times in a row. Typically they call the thunk once per repetition? Actually "every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts." So thunks are called to build arguments, then the function is called repeatedly with those arguments. But if the function reads a file, the file must be present during all repetitions. If the thunk sets a global, that global remains set during the repetitions. But if different cases set the global, there could be interleaving? Usually they measure one case at a time: run thunk, then time many calls. So setting global in thunk is okay as long as the file isn't changed during timing. But to be safe, create separate directories/files for each case and set the global in the thunk. However, the harness may call all thunks first to collect arguments? The instructions say "Thunks run before the timing starts", and "the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts." This suggests for each case, the thunk is called to get the arguments, then the function is called many times with those arguments. It doesn't say all thunks are called at the very beginning. But there is risk: if they call all thunks first, then run each case, the global would be left at the last case's value, and all cases would read the same file (the last one). That would break the different-input design. To avoid this, we could use different `download_dir` values but also... Hmm.

Alternative: Make the function read a file whose content is the same but the workload differences come from `qrel`? But qrel is unused. So the work is solely the file content. We need different file content per case.

Can we avoid global mutations by having the function read a path that depends on the argument? No, path fixed relative to download_dir.

Maybe we can construct one big file and use different qrel sizes? No, work is independent of qrel.

Could we make the function's path different by changing the current working directory? `download_dir` is relative path "ext/download", joined with os.path.join(download_dir, filename). If we change cwd between cases... but the module global download_dir is a relative path; os.path.join would use cwd at call time? Actually `os.path.join` just concatenates strings; gzip.open resolves relative to cwd at open time. So if we change the cwd, the file path resolves differently. But changing cwd is a global process state, and might be acceptable as setup? But it's risky and affects other things. Also cwd change in thunk persists; same interleaving issue, but we could create one directory structure and per-case set cwd? Same problem.

A cleaner approach: create a single large TSV file that contains all different content, but the function reads the entire file every time. To get different work per case, we can vary the file by... can't.

Maybe we can have the thunk itself rewrite the file before returning, and have all repetitions use the same content? But repetitions happen after thunk; the file would be static during repetitions. If we have 8 cases, and each case's thunk rewrites the same file with its own content, then when measuring case A, file has A's content. When measuring case B, thunk B rewrites file. But if the harness runs all thunks first, then the file ends with case H's content and all measure H. That would make all cases identical, not giving diverse work. But maybe the harness runs sequentially: thunk then timing. The phrase "all built and kept in memory before the timing starts" suggests for each case, they build args (thunk) then time. I think it's per-case sequential. But to be safe, we should not rely on global mutation timing? Let's examine typical harness design from these tasks. Usually they have a function `measure(func, cases_list)` where for each case, they call thunk to get args, then run function many times. They may call thunk once per repetition? "every call gets the arguments of its own thunk call" suggests thunk called once per repetition? Actually "each input many times in a row" and "every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts" — sounds like thunk called once, args stored, then function called many times with same args. But "every call gets the arguments of its own thunk call" could mean the thunk is called once per call? That would be expensive (thunk builds data). They say "build large data once, in module-level code, and have the thunk return it". So thunk is cheap and returns prebuilt data. They call thunk before each timed call? Actually "all built and kept in memory before the timing starts" implies args are built once and reused. So one thunk call, many function calls.

Given that, if we rewrite a single file in the thunk, it's rewritten once per case before timing, and during timing it's static. If cases are measured sequentially with their own thunk called just before, it works. But if all thunks are called first, then the last file content is used for all. The risk is real. The safest is to create 8 separate gzip files at module level (or in thunks) and have each thunk set the module global `download_dir` to point to its own directory. But if all thunks are called first, the global would be set to the last directory, and all cases would use that directory. Same problem.

To make it robust regardless of when thunks are called, we need the function to read a different file based on something that persists per call, not a global that gets overwritten. The only per-call state is the arguments passed to the function. The arguments include `qrel`. Could we make `qrel` influence the path? No, the function ignores qrel for path.

Could we monkeypatch? No, forbidden.

Could we make `download_dir` a custom object whose `__fspath__` or string operations depend on something? No, function does `os.path.join(download_dir, "...")`. If download_dir is not a string, os.path.join would call `os.fspath` on it. Could we set `download_dir` to a custom object that returns different paths on successive calls? That would violate "no mocks"? Setting a data field to a custom object that behaves like a string and changes per call... That's kind of a mock/fake environment. Also "Module globals the function reads must be set on the repository's own module" — we can set it to an object. But it's tricky and arguably cheating. Also must be thread-safe etc. Probably overkill.

Maybe the harness guarantees sequential per-case measurement. Most such benchmarks do: for each case, they call thunk to get args, then run the function N times. I think it's fine to set the global in the thunk. But to be extra safe, we can set the global in a way that doesn't depend on execution order? For instance, create one directory containing 8 files with different names, and make the function select by... no.

Alternative: Use the same file but make its content different by having the thunk decompress/compress? No.

Wait: Could we make the file path depend on `qrel` by... no.

Let's think about the harness. The task says: "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs." "Thunks run before the timing starts; only the call of the function is timed." This strongly suggests for each input, they run the thunk (once), then time many calls. They probably iterate: for each case, call thunk, then time. So setting global in thunk is safe.

But there's another instruction: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys ... so every call takes the same path." Here the function doesn't change the file; it only reads. So no issue.

However, if we set `download_dir` in the thunk, and the function doesn't change it, then every call in that case uses the same file. Good.

But the thunk must set the global. Is that considered "setup"? Yes. The instructions allow setting module globals. We just need to ensure the module is imported from the repository, and set its attribute.

Potential issue: The module is imported via `importlib.import_module('extract-msmarco')`. The module name is `extract-msmarco`. We can import it and set `extract_msmarco.download_dir = ...`. But the function under test is `load_msmarco_queries`. The harness will import it itself? The task says "Import it as `load_msmarco_queries = importlib.import_module('extract-msmarco').load_msmarco_queries`". That means the harness will do that. Our code should import the module to set globals. We can do `import importlib; mod = importlib.import_module('extract-msmarco')`. But we should be careful: our code is run in the same process as the harness? Probably our code is exec'd, then the harness imports the function. Setting globals should be done on the same module object. If we import it, we get the module object; the harness later does `importlib.import_module('extract-msmarco')`, which returns the same cached module (since sys.modules). So setting `mod.download_dir` persists. Good.

Now, what's the realistic workload? We need 8 cases with different sizes/content. The function reads a gzip TSV. Let's design 8 files with varying:
- number of lines (e.g., 5k, 20k, 50k, 100k, 200k?) But total build time under 10s. Creating 8 gzip files with total ~ maybe 500k lines is fine.
- query strings with different character classes: lots of punctuation (to trigger regex sub), uppercase (lowercase), unicode word chars? `\w` in Python 3 with default re is Unicode-aware? Actually `re` with str uses Unicode by default for `\w`. So we can include accented letters, Cyrillic, etc. The regex `[^\w ]` matches non-word, non-space. So `\w` includes letters/digits/underscore. We can test with punctuation, emojis, etc.
- different query lengths.
- duplicate query strings (so dictionary overwrites? queryid unique; duplicates of query text but different ids; that's realistic).
- empty lines? The csv reader with delimiter tab; if a line has no tab, `for [queryid, query] in tsvreader` would raise ValueError (not enough values to unpack). So every line must have exactly two fields. Real MS MARCO file has queryid and query. Could have empty query string (just tab). That's allowed: `["123\t"]` -> queryid="123", query="". Then re.sub on empty string.
- Lines with more than one tab? `csv.reader` would return more than two fields, unpacking fails. So avoid.
- Query strings with tabs? Tab is delimiter so no.
- Very long query strings (e.g., 10k chars) to stress regex and memory.

We need to make sure the function's output (a dict of queryid -> processed query) is under 100k values. If file has 200k lines, output dict 200k entries > 100k. So keep lines <= 100k, or output could exceed. Actually limit says "keep what it returns ... under about 100 000 values". So output dict size must be <= 100k. So max lines maybe 80k. That's fine, 80k lines might take ~50-100ms. Good.

We can have cases with different line counts: 5k, 10k, 20k, 40k, 80k, etc. Also different content complexity.

We need to build the gzip files. Use `gzip.open(path, "wt", encoding="utf8")`. Generate lines with `random.Random(seed)`.

Also we need `qrel` argument. Real caller passes `query_relevance = load_msmarco_qrels()`, which likely is a dict mapping queryid to relevance judgments. It's unused, but we should pass a realistic dict so argument rendering is realistic. We can create a dict of same queryids? But if we make qrel large, argument rendering (repr) could be big. Keep it moderate, maybe a few thousand entries. Or we could just pass an empty dict or None? The function accepts anything; it doesn't use it. For checks, we can test with None. For cases, pass a dict with some size. But since it's unused, size doesn't affect function work, only rendering overhead. The instructions say keep arguments data under 1M values. A dict of 80k entries is fine but repr might be large; but they render arguments before and after each call. That could be expensive if qrel is huge. Better keep qrel small (e.g., 1000 keys) to not dominate setup/rendering. But is it realistic? In the repo, qrel is the full qrels file, which could be large. However, the function doesn't use it, so we can pass a small dict. The comparison of outputs after every input includes the function's return (queries dict). That's what matters. The arguments are rendered "to see whether it changed them". If qrel is not modified, rendering it each time adds overhead but not timing. But it could bloat memory. Keep it small.

Actually, to be safe and realistic, we could make qrel a dict with the same queryids as the file, but that duplicates. Hmm. Let's just make qrel a small dict with some entries; the function doesn't care.

But wait: the function's signature `load_msmarco_queries(qrel)`. The caller does `load_msmarco_queries(query_relevance)`. So qrel is the query relevance data. We can create a dict with a few thousand entries. For 8 cases, we can reuse the same qrel dict, or vary. Since unused, one shared dict is fine. But "each case should make the function do substantial and different work" — the work is file reading; qrel doesn't affect. So the difference is in file content and size.

Now, let's design 8 cases:

1. "tiny-queries": many short queries (e.g., 1-3 words), 20k lines, little punctuation.
2. "long-queries": queries with long strings (100-500 chars), 10k lines.
3. "punctuation-heavy": queries with lots of punctuation (to exercise regex sub), 30k lines.
4. "unicode": queries with accented letters, Cyrillic, Chinese, emojis (to test `\w` Unicode), 20k lines.
5. "uppercase": queries in uppercase (to exercise `.lower()`), 40k lines.
6. "many-lines": 80k lines of medium queries (stress dictionary sizing).
7. "duplicates": many duplicate query strings but different ids? Actually ids unique, query text duplicates. The dict keys are ids, so no collision. Duplicate text doesn't reduce work because re.sub/lower done per line. Could be realistic. 50k lines.
8. "empty-and-short": lines with empty query string, single char, etc. 30k lines.

We must ensure each line has exactly one tab. Query strings can contain spaces (allowed), no tabs.

Also note: `re.sub(r"[^\w ]", " ", query).lower()`. The `\w` matches [a-zA-Z0-9_] plus Unicode word chars. Space is allowed. Everything else replaced with space. Lowercasing after substitution. If we include punctuation, it becomes spaces. The output dict values will have many spaces.

For stress, we could include digits, underscores. `\w` includes underscore, so underscore stays. Punctuation removed.

We need to create the gzip files. Where? Under WORKDIR. We can create a directory per case under `WORKDIR / "case0"` etc. Then set `mod.download_dir = str(WORKDIR / "caseN" / "ext" / "download")`? Actually download_dir is joined with "msmarco-doctrain-queries.tsv.gz". So we can set download_dir to `str(WORKDIR / "caseN")` and put the file directly there. But the original code does `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")`. So download_dir is the directory. We'll set it to a directory containing that file. Use `WORKDIR / f"case{i}"`, and file `msmarco-doctrain-queries.tsv.gz` inside.

But wait: The module also has other functions that use `download_dir`. We only test `load_msmarco_queries`. So setting it is fine.

Now, the thunk must set `mod.download_dir` and return `(qrel,)`. But if the harness calls thunks sequentially, we need to make sure the correct file is present. We'll create all files at module level. Then each thunk sets the global and returns args.

But there's a catch: the thunk sets a global. If the harness calls the thunk once per repetition (many times), it would set the global each time. That's fine, just redundant. If it calls the thunk once, then times, fine.

Potential issue: If the harness measures cases in parallel? No, "each input many times in a row" suggests sequential. So global mutation is safe.

Alternatively, to avoid global mutation entirely, we could create a single directory and have each case use a different *file name* by... no, filename fixed. Could we set `download_dir` to a path that includes a symlink that changes? No.

Another approach: Use `os.path.join(download_dir, ...)` where `download_dir` is a string. We could set `download_dir` to a string that points to a different file via `os.path` tricks? No.

I think thunk setting global is acceptable and standard for these tasks. The example in the prompt for `Index.lookup` sets `search.index.CASE_SENSITIVE = False` at module level, not per thunk. But it also uses different files? It uses one _VOCAB. For per-case different files, they'd have to set global per thunk or use different module-level setup. In the example, they used `itertools.count()` to vary words per thunk call, not global. For our function, the only way to vary file content is to change the path or rewrite the file. Setting a global per thunk is a natural way.

But let's reconsider: Could we create one gzip file containing all lines, and have the function process the whole file each time? Then all cases would be identical. Not good.

Could we make the thunk rewrite the *same* file with different content? That would be a single file path, no global change. The thunk would `gzip.open(path, "wt").write(...)`. This is setup, done before timing. If the harness calls thunk once per case before timing, the file is set for that case. If it calls all thunks first, the last write wins. Same risk. But with a single file, we don't mutate a global; however, the file content persists. The risk is identical. But maybe the harness runs cases sequentially; either way works. Which is safer? Mutating a global could affect other cases if they share globals? They don't. Rewriting a file is also fine.

Actually, rewriting a single file has a subtle issue: if the harness measures multiple cases interleaved? Unlikely. Also, if the function is run many times in a row, the file is static. So both approaches equivalent.

But there's another consideration: "Anything the function changes outside its arguments ... carries over from one call to the next". The function doesn't change the file. So rewrite in thunk is fine.

I think using separate directories and setting `download_dir` per thunk is cleaner and avoids I/O in the thunk (just an assignment). Building files at module level also ensures setup time is outside timing. The harness will call thunk which does an assignment and returns args. Very cheap.

Let's check if the module name with hyphen works. `importlib.import_module('extract-msmarco')` — does that work? The task says it does. We'll use that. But we must ensure the module file is on sys.path. The task says "Import the repository's modules exactly as shown in the task." So we do `import importlib; extract_msmarco = importlib.import_module('extract-msmarco')`. But wait: the module is in `text-search/python/extract-msmarco.py`. Is that directory on sys.path? The task says import as shown, so presumably the harness sets sys.path. We just use the importlib call.

Now, we need to set `download_dir` on that module. Initially it's `os.path.join("ext", "download")`. We'll override.

Let's plan the code structure:

```python
import gzip
import importlib
import os
import random

extract_msmarco = importlib.import_module('extract-msmarco')

# Build data files under WORKDIR
_BASE = WORKDIR / "msmarco_queries"
_BASE.mkdir(exist_ok=True)

def _make_file(case_name, lines):
    d = _BASE / case_name
    d.mkdir(exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    with gzip.open(path, "wt", encoding="utf8") as f:
        for qid, query in lines:
            f.write(f"{qid}\t{query}\n")
    return d

# But we need to build files with random content. Let's write generator functions.

_rng = random.Random(0)

def _generate_queries(n, mode, seed):
    rng = random.Random(seed)
    lines = []
    for i in range(n):
        qid = str(i + 1)  # unique
        # generate query according to mode
        ...
    return lines
```

We need 8 cases. Let's define generation functions for different modes.

We need to be careful with line counts and output values. We'll keep each file under 80k lines, total build time okay.

Let's estimate gzip compression time: writing 80k short lines maybe 0.1s. Total 8 files maybe <1s. Good.

Now, regex: The function uses `re.sub(r"[^\w ]", " ", query)`. Python's re module caches compiled patterns, so first call compiles. But since we run many times, first is negligible.

We need realistic query strings. MS MARCO queries are natural language questions, e.g., "what is the capital of france". So words, spaces, question marks. Punctuation like `?`, `,`, `.`, `!`, apostrophes, hyphens. Also numbers.

Let's design modes:

1. "short": 1-5 words, mostly letters, some question marks. 20,000 lines.
2. "medium": 5-15 words, punctuation. 40,000 lines.
3. "long": 50-200 words, strings length 500-2000 chars. 5,000 lines (output 5k values). This stresses regex sub on long strings.
4. "punctuation": strings with lots of symbols: `!@#$%^&*()_+-=[]{};':",./<>?` etc. 30,000 lines.
5. "uppercase": all uppercase letters, no punctuation. 30,000 lines.
6. "unicode": mix of accented, Cyrillic, Greek, Chinese, emojis, etc. 20,000 lines.
7. "empty-short": some lines with empty query string, some single char, some just spaces. 30,000 lines.
8. "huge": 80,000 lines of medium complexity. This is the largest.

Wait, output dict size equals number of lines (since queryid unique). For case 8, 80k entries, under 100k. OK.

But total lines across all files: 20k+40k+5k+30k+30k+20k+30k+80k = 255k lines. Building all files maybe 0.5-1s. Fine.

We also need `qrel` for each case. Could be a shared dict. Let's make a realistic qrel dict with maybe 10,000 entries mapping queryid to 1/0. But since unused, we can just use a dict of a few thousand. To keep argument rendering cheap, maybe 1,000 entries. But the instructions say "prepare the way the repository's own callers do". The caller passes the full qrels. But we can't easily load the real qrels. We can create a synthetic qrel with queryids matching some of the file's ids. However, since unused, its size doesn't affect function work. I'd make it moderately sized, e.g., 5,000 entries, to be realistic but not huge. But rendering a dict of 5,000 entries before/after each call might take some time but not timed. Memory fine.

Actually, we can just pass the same dict for all cases. But the thunk returns `(qrel,)`. If qrel is shared and not modified, fine.

But wait: The harness compares outputs in full. If qrel is huge, they might also render it. But they said arguments are rendered before/after each call. That could be expensive if qrel is huge. Keep it small, like 1000.

Alternatively, we could pass `None` as qrel? The function accepts anything. But the real caller passes a dict. "Realistic" suggests dict. Let's make a dict of 1000 entries mapping str(i) to i%2.

But the queryids in the file are str(i+1). So qrel keys could be a subset. Doesn't matter.

Now, checks(): 2 or 3 small edge inputs, checked only for identical behaviour, never measured. These may raise. But the function under test reads a file. If we give an empty or malformed file, it may raise. We can create small files for checks.

Check cases must run to completion? "checks(): 2 or 3 small edge inputs ... checked only for identical behaviour, never measured. These may raise." So we can have cases that raise, e.g., a file with a line missing a tab -> ValueError. Or a file that doesn't exist -> FileNotFoundError. But "checked only for identical behaviour" means original and modified should behave the same (both raise or both return). We can include:
- empty file: gzip file with no lines -> returns empty dict `{}`.
- one line: single query -> returns dict with one entry.
- malformed line (no tab) -> raises ValueError.

But we must ensure the module global `download_dir` is set for these checks too. Since checks are run separately, we need to set the global for each check thunk. The thunk can set `extract_msmarco.download_dir` to a directory containing the edge file.

We'll create small files for checks at module level.

Now, let's think about the thunk design. Each thunk must set the global and return `(qrel,)`. But the global setting is a side effect. If the harness calls the thunk multiple times, it sets it each time, fine. If the harness runs checks before cases, the global might be left at a check's directory, but each case thunk sets it again. So fine.

However, there is a potential problem: The harness might call the thunk to get arguments, then run the function many times. But if the function reads the file, and the file is modified by another case's thunk in between? If cases are measured sequentially, no. If interleaved, bad. But assume sequential.

To be maximally robust, we could avoid changing the global per case by having a single directory but different files for each case, and use a global that selects the file based on something else? No.

Another idea: Use `download_dir` as a path that contains a symlink to a different file? No.

What if we set `download_dir` to a directory and create a file `msmarco-doctrain-queries.tsv.gz` that is a *compressed stream* concatenating multiple gzip members? gzip can contain multiple members. The function reads all. But that doesn't allow per-case variation.

Maybe we can use `download_dir` as a `pathlib.Path`? `os.path.join` works with Path. No.

I think per-thunk global setting is acceptable. Many similar tasks do this.

But wait: The instructions say "Module globals the function reads must be set on the repository's own module". It doesn't say we can't set them in thunks. It says "Setting data (a module's configuration, an object's fields) to build an input is fine." So setting `download_dir` in the thunk is explicitly allowed.

Now, the `download_dir` is read at call time inside the function. If we set it in the thunk before the call, it's set. The function doesn't modify it. So repeated calls use the same directory. Good.

Now, let's write the code.

First, import modules:

```python
import gzip
import importlib
import os
import random

extract_msmarco = importlib.import_module('extract-msmarco')
```

But the task says "Import it as `load_msmarco_queries = importlib.import_module('extract-msmarco').load_msmarco_queries`". That's for the harness. In our code, we need to set globals on the module. We can do `_mod = importlib.import_module('extract-msmarco')`. But careful: if the harness later imports it, it gets the same module object. Our code runs in the same process? Yes, the harness executes our code, then imports the function. So it's the same.

Actually, the harness might import the module itself first, then run our code? Either way, `sys.modules` has one instance. We'll import and set.

Now, WORKDIR is provided as a `pathlib.Path`. We use it in module-level code.

Let's define `_BASE = WORKDIR / "extract_msmarco_inputs"`. We'll create subdirectories for each case and check.

Building files:

We need to generate queries with different characteristics. Let's define helper functions.

For realistic query strings, we can use a word list. We'll generate random words from a small vocabulary and add punctuation.

Let's define:

```python
_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "what", "is", "capital", "of", "france", "how", "to", "make",
    "pasta", "best", "movie", "2023", "weather", "new", "york",
    "python", "programming", "language", "data", "science", "machine",
    "learning", "artificial", "intelligence", "neural", "network",
    "computer", "algorithm", "database", "network", "security",
    "hello", "world", "example", "test", "query", "search", "engine",
]
```

We can add some words with underscores, digits, etc.

For each mode:

- `_gen_short(rng, n)`: for each line, pick 1-4 words, join with space, optionally append "?".
- `_gen_medium(rng, n)`: 5-15 words, add commas, periods, question marks.
- `_gen_long(rng, n)`: for each line, generate a long string of 500-3000 chars by repeating words with spaces and punctuation.
- `_gen_punct(rng, n)`: generate strings with many punctuation marks. E.g., start with a word, then add random punctuation chars from a set.
- `_gen_upper(rng, n)`: like medium but uppercase.
- `_gen_unicode(rng, n)`: use a set of unicode words: "café", "naïve", "München", "Москва", "Ελλάδα", "北京", "こんにちは", "안녕하세요", "hello", "résumé", "façade", "jalapeño", plus emojis. Note: emojis are not `\w`, so they get replaced by space. That's fine.
- `_gen_empty_short(rng, n)`: mix of empty strings, single char, spaces, and short words.
- `_gen_huge(rng, n)`: like medium, 80k lines.

We must ensure that query strings do not contain tabs or newlines. Our generated words don't. Punctuation we add should not include tab/newline. Fine.

Also, queryid must be unique. We'll use str(i+1). To add some variety, we can use random-looking ids, but sequential is fine. However, the real MS MARCO query ids are like "1048578" etc. We can use `str(rng.randint(1000000, 9999999))` but must ensure uniqueness. Simpler: `str(i + 1000000)`. But duplicates would overwrite in dict (if same id). The function does `queries[queryid] = query`, so duplicate ids would reduce output size. To keep output size = number of lines, use unique ids. Sequential is unique. The real ids are not sequential in file? They are arbitrary but unique. We can use `str(1000000 + i)`.

Now, for the file writing, we need to write lines. Use `gzip.open(path, "wt", encoding="utf8")`. The function opens with "rt", encoding="utf8". So we match encoding.

Now, building all files at module level. We can define a list of (case_name, generator, n). Then create directories and write.

But we need to be careful: the gzip file must be fully written and closed before any call. We write at module level, so fine.

Now, the thunks:

For each case, we have a directory `_dirs[case_name]`. The thunk:

```python
def _make_thunk(directory, qrel):
    def thunk():
        extract_msmarco.download_dir = str(directory)
        return (qrel,)
    return thunk
```

But the instructions say: "A thunk takes no arguments and returns a tuple of positional arguments for the function". So `lambda: (qrel,)` but we need to set global. A lambda can do that? We can use a function or lambda with side effect? It's better to use a small function. The examples use `lambda: (Index(_VOCAB), _words(...))`. They don't show side effects. But we can define a function.

However, note: "A thunk takes no arguments and returns a tuple..." It doesn't forbid side effects. But we must ensure the thunk is cheap. Setting a global is cheap.

But there's a subtlety: If the harness calls the thunk once per repetition, and the thunk sets the global each time, that's fine. But if the harness calls all thunks first to build a list of args, then it would call thunk for each case, and the global would end up as the last case's directory. Then all cases would use the same file. To avoid this, we should not rely on the global being set by the thunk at call time; instead, we can set the global at module level to the correct directory for each case, but that's impossible for multiple cases.

Wait, could we make the thunk return a *copy* of the module's `download_dir`? No, the function reads the global.

Let's think more carefully about how the harness likely works. The task description: "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs." This implies for each input, they run the function many times. The thunk is used to get the arguments. It says "Thunks run before the timing starts; only the call of the function is timed." This could mean for each input, the thunk runs once before the timing loop. So for each input sequentially: call thunk, then time N calls. That's the natural implementation. In that case, setting the global in the thunk works perfectly.

If they instead did: args = [thunk() for _, thunk in cases]; then for each args_i: time N calls. Then the global would be whatever the last thunk set. That would be a flawed harness because it would break any stateful setup. But the instructions explicitly warn about stateful things: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys ... so every call takes the same path." This warning is about the function changing state between calls. It implies they run the function many times with the same args, and state changes persist. They expect the thunk to set up the state before timing. If they ran all thunks first, then the state from the last thunk would persist across all cases, which would be bad. So likely they run thunks per case just before timing. I'll assume that.

However, there's still a risk: if the thunk is called multiple times (e.g., once per repetition), the global will be set correctly each time. Fine.

To be even safer, we could avoid using a module global that is overwritten by different cases by making the function read a file whose content is determined by the argument. But the function doesn't use the argument for path. So impossible.

Alternatively, we could create a single directory with 8 different files, and use a symlink "msmarco-doctrain-queries.tsv.gz" that points to the desired file. The thunk would change the symlink target. That's still a global file state, similar to global variable. If all thunks run first, the symlink points to the last file. Same issue.

Maybe we can make the function see different files by changing the current working directory? `download_dir` is relative. If we set `download_dir = "ext/download"` (default) and vary cwd, then `os.path.join("ext/download", filename)` resolves relative to cwd at open time. The thunk could change cwd. Same global state issue.

Given all approaches have the same limitation, I'll go with setting the module global. It's the most direct and follows the instructions.

Now, let's write the generation functions. We must ensure no line causes an exception due to unpacking. So each line must have exactly one tab. Our strings must not contain tab. Punctuation we add should not include tab. We'll use safe characters.

Let's define a helper to generate a random word from a vocabulary, possibly with punctuation.

For punctuation-heavy, we can include characters: `!@#$%^&*()_+-=[]{};':",./<>?` and backslash, vertical bar, tilde, backtick. But avoid tab and newline. Also avoid non-ASCII if not needed.

For unicode, we can include characters that are `\w` (like accented letters, Cyrillic, Chinese) and some that are not (emojis, punctuation). That's realistic.

For long queries, we can just repeat random words many times.

Let's write the code.

```python
import gzip
import importlib
import os
import random

_MOD = importlib.import_module('extract-msmarco')
_BASE = WORKDIR / "msmarco_queries"

# Vocabulary
_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "what", "is", "capital", "of", "france", "how", "to", "make",
    "pasta", "best", "movie", "2023", "weather", "new", "york",
    "python", "programming", "language", "data", "science", "machine",
    "learning", "artificial", "intelligence", "neural", "network",
    "computer", "algorithm", "database", "security", "hello", "world",
    "example", "test", "query", "search", "engine", "information",
    "retrieval", "ranking", "evaluation", "performance", "system",
    "user", "interface", "design", "pattern", "architecture",
]

_PUNCT = list("!@#$%^&*()_+-=[]{};':\",./<>?\\|`~")

_UNICODE_WORDS = [
    "café", "naïve", "München", "Москва", "Ελλάδα", "北京", "こんにちは",
    "안녕하세요", "résumé", "façade", "jalapeño", "über", "señor",
    "😀", "🎉", "🚀", "❤️", "日本", "中国", "España", "Français",
    "Ünïcödé", "test123", "hello_world", "foo_bar",
]
```

Now generators:

```python
def _gen_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(1, 4)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.3:
            q += "?"
        if rng.random() < 0.2:
            q = q.capitalize()
        lines.append((qid, q))
    return lines

def _gen_medium(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(5, 15)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        # add some punctuation
        if rng.random() < 0.5:
            q += rng.choice([".", "?", "!", ","])
        if rng.random() < 0.3:
            # insert comma
            pos = rng.randint(0, len(q)-1)
            q = q[:pos] + "," + q[pos:]
        lines.append((qid, q))
    return lines

def _gen_long(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        target_len = rng.randint(500, 3000)
        parts = []
        total = 0
        while total < target_len:
            w = rng.choice(_WORDS)
            parts.append(w)
            total += len(w) + 1
            if rng.random() < 0.1:
                parts.append(rng.choice(_PUNCT))
        q = " ".join(parts)
        lines.append((qid, q))
    return lines

def _gen_punct(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 10)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        # insert random punctuation between words and inside
        chars = list(q)
        for _ in range(rng.randint(5, 20)):
            pos = rng.randint(0, len(chars))
            chars.insert(pos, rng.choice(_PUNCT))
        q = "".join(chars)
        lines.append((qid, q))
    return lines

def _gen_upper(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_WORDS).upper() for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines

def _gen_unicode(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_UNICODE_WORDS) for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines

def _gen_empty_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        r = rng.random()
        if r < 0.1:
            q = ""
        elif r < 0.3:
            q = rng.choice([" ", "  ", "   "])
        elif r < 0.5:
            q = rng.choice("abcdefghijklmnopqrstuvwxyz")
        else:
            k = rng.randint(1, 3)
            q = " ".join(rng.choice(_WORDS) for _ in range(k))
        lines.append((qid, q))
    return lines

def _gen_huge(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(4, 12)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.4:
            q += "?"
        lines.append((qid, q))
    return lines
```

Now, we need to write these to gzip files. We'll create a dictionary `_DIRS = {}` mapping case label to directory path.

```python
_CASES_SPEC = [
    ("short", _gen_short, 20_000),
    ("medium", _gen_medium, 40_000),
    ("long", _gen_long, 5_000),
    ("punct", _gen_punct, 30_000),
    ("upper", _gen_upper, 30_000),
    ("unicode", _gen_unicode, 20_000),
    ("empty-short", _gen_empty_short, 30_000),
    ("huge", _gen_huge, 80_000),
]

for label, gen, n in _CASES_SPEC:
    d = _BASE / label
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    rng = random.Random(0)  # fixed seed for generation? But we use separate seed per case? 
    # Actually we should use a fixed seed per generator, but the generator functions take rng.
    # We can pass a fresh random.Random(seed) for each.
```

But the instruction says "use a fixed random seed (`random.Random(0)`) when generating data." So we should use `random.Random(0)` for each generation? Or one global? Typically, each case can have its own seed, but fixed. We can use `random.Random(0)` inside each generator call. But if we pass the same rng sequentially, the state carries over. That's fine as long as it's deterministic. The instruction says "use a fixed random seed (random.Random(0))". I'll create a new `random.Random(0)` for each case to make each independent? Or use a single `random.Random(0)` for all? The example uses different seeds per case (`_rows(2_000, 4, 0)` and `_rows(5_000, 4, 1)`). So different seeds per case are fine. I'll use seed = index. But the instruction literally says `random.Random(0)`. I'll use a fixed seed per case, maybe the case index. To be safe, I'll use `random.Random(0)` for the first case, `random.Random(1)` for second, etc. Or just `random.Random(0)` for all? Using the same seed for all cases with different generators would still produce different content because the generators consume different numbers of random numbers. But it's cleaner to use different seeds. The instruction says "a fixed random seed (`random.Random(0)`)". I'll use `random.Random(0)` for each case? Actually if I call `random.Random(0)` anew for each case, they all start from the same state, but since the generation functions differ, the outputs differ. That's fine. But if two cases use the same generator function with the same n, they'd produce identical data. Our cases use different generators or different n, so okay. However, to add diversity, I'll use different seeds: `random.Random(i)` for case i. The instruction says `random.Random(0)` as an example; "a fixed random seed" means deterministic. So different seeds are fine as long as fixed.

Let's use `rng = random.Random(seed)` where seed = index.

Now, writing:

```python
_WRITE_SPEC = [
    ("short", _gen_short, 20_000, 0),
    ("medium", _gen_medium, 40_000, 1),
    ("long", _gen_long, 5_000, 2),
    ("punct", _gen_punct, 30_000, 3),
    ("upper", _gen_upper, 30_000, 4),
    ("unicode", _gen_unicode, 20_000, 5),
    ("empty-short", _gen_empty_short, 30_000, 6),
    ("huge", _gen_huge, 80_000, 7),
]

_DIRS = {}
for label, gen, n, seed in _WRITE_SPEC:
    d = _BASE / label
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    rng = random.Random(seed)
    lines = gen(rng, n)
    with gzip.open(path, "wt", encoding="utf8") as f:
        for qid, query in lines:
            f.write(f"{qid}\t{query}\n")
    _DIRS[label] = d
```

Now, the qrel. We need a dict. Let's make a small realistic one:

```python
_QREL = {str(1_000_000 + i): i % 2 for i in range(1000)}
```

But wait: the function doesn't use qrel, so its size is irrelevant. However, the function is called with `qrel` as the only argument. The harness will render arguments before/after. A dict of 1000 entries is fine.

But to be more realistic, the qrel might be larger. The real qrels file for MS MARCO doc train has ~ 397k entries. But we don't want to render 397k entries each time. The instruction says "keep each input's data under about 1 000 000 values." 397k is under 1M. But rendering 397k entries before/after each call could be slow. However, it's not timed, but setup? The rendering is part of the comparison, not timing. It might take time but not affect energy measurement? Actually the harness measures energy of the function call only. Rendering arguments is outside timing. But if rendering is slow, it might slow down the overall experiment but not energy. Still, we can keep it moderate. I'll use 10,000 entries to be safe.

Actually, let's reconsider: The function signature is `load_msmarco_queries(qrel)`. The qrel argument is completely unused. The real caller passes `load_msmarco_qrels()`, which returns a dict of queryid -> relevance. Since it's unused, we could pass an empty dict or a small dict. To minimize overhead, use a small dict, e.g., 100 entries. But the instruction says "build real inputs; never replace code". A small qrel is still a real dict. I'll use 1000.

Now, the thunks.

For each case label, we need a thunk that sets `_MOD.download_dir = str(_DIRS[label])` and returns `(_QREL,)`.

But we must be careful: `_QREL` is a shared dict. The function doesn't modify it, so fine. But if the harness checks that arguments are unchanged, they will compare the dict before and after. Since it's unchanged, fine.

Now, checks():

We need 2 or 3 small edge inputs. They are checked only for identical behaviour, never measured. They may raise.

Let's create:
1. "empty-file": gzip file with no lines. Returns `{}`.
2. "one-line": gzip file with a single line "1\thello world". Returns `{"1": "hello world"}`.
3. "malformed": gzip file with a line missing a tab, e.g., "no-tab-here". This will cause `ValueError: not enough values to unpack (expected 2, got 1)`. Both original and modified should raise.

But we must ensure the modified version also raises similarly. That's the check. Good.

We need to create these files under WORKDIR. Let's create `_CHECK_DIRS`.

```python
_CHECK_BASE = WORKDIR / "msmarco_queries_checks"

def _make_check_file(name, lines):
    d = _CHECK_BASE / name
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    with gzip.open(path, "wt", encoding="utf8") as f:
        for line in lines:
            f.write(line + "\n")
    return d

_CHECK_DIRS = {
    "empty": _make_check_file("empty", []),
    "one": _make_check_file("one", ["1\thello world"]),
    "malformed": _make_check_file("malformed", ["this is not a tsv line"]),
}
```

Wait, the malformed line "this is not a tsv line" has no tab, so csv.reader returns `['this is not a tsv line']` (single field). Then `for [queryid, query] in tsvreader` tries to unpack a list of length 1 into 2 variables -> ValueError. Good.

But what if the line has spaces? csv.reader with delimiter "\t" will treat the whole line as one field. Yes.

Now, checks() returns list of (label, thunk). The thunk sets the global and returns `(qrel,)`. For checks, we can use the same `_QREL` or a tiny one. Since not measured, fine.

```python
def checks():
    return [
        ("empty-file", lambda: (_set_dir_and_return(_CHECK_DIRS["empty"]), _QREL)[1]),
        ...
    ]
```

Better define a helper:

```python
def _thunk_for(directory, qrel=_QREL):
    def thunk():
        _MOD.download_dir = str(directory)
        return (qrel,)
    return thunk
```

Then:

```python
def checks():
    return [
        ("empty-file", _thunk_for(_CHECK_DIRS["empty"])),
        ("one-line", _thunk_for(_CHECK_DIRS["one"])),
        ("malformed", _thunk_for(_CHECK_DIRS["malformed"])),
    ]
```

But careful: `_QREL` is a shared dict. The function doesn't modify it. But if the harness checks argument mutation, it will see no change. Good.

Now, cases():

```python
def cases():
    return [
        ("short", _thunk_for(_DIRS["short"])),
        ("medium", _thunk_for(_DIRS["medium"])),
        ("long", _thunk_for(_DIRS["long"])),
        ("punct", _thunk_for(_DIRS["punct"])),
        ("upper", _thunk_for(_DIRS["upper"])),
        ("unicode", _thunk_for(_DIRS["unicode"])),
        ("empty-short", _thunk_for(_DIRS["empty-short"])),
        ("huge", _thunk_for(_DIRS["huge"])),
    ]
```

We need exactly 8 measured inputs.

Now, let's verify the output sizes. Each file has n lines, and each queryid is unique (sequential). So output dict has n entries. For "huge", n=80,000. Under 100,000. Good. For others, less.

But wait: the "empty-short" generator might produce duplicate queryids? No, qid = str(1_000_000 + i) unique per line.

Now, check the regex: `re.sub(r"[^\w ]", " ", query).lower()`. If query contains characters like `\` or `|`, they get replaced. Fine.

Now, potential issue: The function uses `csv.reader(f, delimiter="\t")`. Our file has lines like `1000000\tsome query`. The query may contain spaces and punctuation. That's fine. But what if the query contains a tab? We must ensure no tab. Our _PUNCT list does not include tab. Our unicode words don't include tab. Good.

What about carriage returns? We write with "\n". gzip.open in text mode with default newline handling? When writing "wt", it translates \n to os.linesep? Actually gzip.open with "wt" uses io.TextIOWrapper with default newline=None, which translates \n to os.linesep on write? Let's recall: `gzip.open(filename, "wt")` returns a text wrapper with newline=None, which means universal newlines on read, and on write, \n is translated to os.linesep? Actually for writing text, newline=None means any \n written is translated to os.linesep. On Windows, it would write \r\n. But the function opens with "rt" and newline default (None), which means universal newlines: it will translate \r\n to \n. So that's fine. But to be safe, we can open with newline=""? Not necessary.

However, the function's `csv.reader` might see the trailing newline? csv.reader handles newlines. It yields the row without newline. So fine.

Now, we need to ensure the files are under WORKDIR. We use `WORKDIR / "msmarco_queries"`. The function will read from `download_dir` which we set to `_DIRS[label]`. `_DIRS[label]` is a Path object; we set `_MOD.download_dir = str(directory)`. The function does `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")`. Since download_dir is a string, it works.

Now, what about the module's original `download_dir = os.path.join("ext", "download")`. We override it. That's setting a module global. Allowed.

Now, let's consider the energy measurement. The function prints "Loading queries..." each call. That's a side effect. The harness runs many calls. The print statement goes to stdout. That's fine, but it might slow down? Printing is I/O, could be slow. But it's part of the function, so it's measured. The original function has the print. We cannot change it. It will print many times, potentially flooding stdout. But the harness likely captures or ignores. It's part of the work.

Now, one more thing: The function reads the file every call. That's the main work. Our thunk sets the global. But what if the harness runs the original and modified versions separately? They might run original on the 8 inputs, then modified on the same 8 inputs. The thunks will be called again for the modified run. The global is set again. Fine.

Now, let's double-check the generation functions for any potential exception. For `_gen_long`, we create a list of parts and join with " ". The target_len can be up to 3000. The number of parts could be large but fine. The query string length could be ~3000. The regex sub on a 3000-char string is fine.

For `_gen_punct`, we insert punctuation into the string. The string could become long if we insert many. Max ~ 10 words * 6 chars + 20 punct = 80 chars. Fine.

For `_gen_unicode`, we use emojis like "❤️" which contains variation selector, not `\w`. That's fine.

Now, let's think about the "huge" case: 80,000 lines. The output dict has 80,000 entries. The function also reads 80,000 lines, does regex sub, lower, and dict assignment. This might take around 0.1-0.2 seconds. Under 1s. Good.

But wait: The instruction says "One call should take roughly 1 ms to 200 ms on the original." 80,000 lines might take more than 200ms? Let's estimate. In Python, reading a gzip file with 80,000 lines, each line maybe 20-40 chars. Decompression is fast (gzip is C). csv.reader is Python but implemented in C? Actually csv.reader is a C extension in CPython? The `_csv` module is C. So reading 80k lines is fast. For each line, `re.sub` and `.lower()` and dict assignment. `re.sub` on a short string is fast. 80k iterations might take ~0.05-0.15s. I think it's fine. If it's too slow, we could reduce to 60,000. But 80k is likely okay. Let's keep 80k.

Actually, let's be conservative. The instruction says "One call should take roughly 1 ms to 200 ms". 200ms is the upper end of "roughly". 80k lines might be close to 200ms. To be safe, maybe 60,000. But we want 8 diverse cases. We can have the largest be 70,000. Let's calculate: 70,000 lines, each ~30 chars. A quick benchmark mentally: Python can do ~1 million simple dict assignments per second? Actually, Python loop overhead is significant. 100,000 iterations of simple operations might take ~0.05s. Regex sub might double it. So 80k ~ 0.1s. That's fine.

Now, let's consider the output dict size limit: "keep what it returns ... under about 100 000 values." 80k is under 100k. Good.

Now, the arguments: qrel is a dict of 1000 entries. The harness renders arguments before and after. That's fine.

Now, we need to make sure the module is imported correctly. The file name is `extract-msmarco.py`. `importlib.import_module('extract-msmarco')` should work if the directory is on sys.path. The task says to import it as shown. So we use that.

But wait: In our code, we do `_MOD = importlib.import_module('extract-msmarco')`. Is that module in sys.path? The task says "Import the repository's modules exactly as shown in the task." So the harness presumably sets up sys.path. It should work.

Now, let's write the complete code in a single Python block.

We need to define `checks()` and `cases()`. The module-level code runs before. We'll include all the generation and file writing at module level.

One more thing: The thunk sets `_MOD.download_dir`. But the thunk is defined in our module. The `_MOD` variable is a module object. That's fine.

But careful: The thunk returns `(qrel,)`. The harness calls the function with positional arguments. So `load_msmarco_queries(qrel)`. That matches.

Now, let's consider the "empty-short" case: some lines have empty query string. The function does `re.sub(r"[^\w ]", " ", "").lower()` -> "". Then `queries[qid] = ""`. Fine.

Now, let's write the code.

We'll also need to ensure that the directories are created under WORKDIR. We use `WORKDIR / "msmarco_queries"`. WORKDIR is provided.

Now, let's write it out.

```python
import gzip
import importlib
import random

_MOD = importlib.import_module('extract-msmarco')

_BASE = WORKDIR / "msmarco_queries"

_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "what", "is", "capital", "of", "france", "how", "to", "make",
    "pasta", "best", "movie", "2023", "weather", "new", "york",
    "python", "programming", "language", "data", "science", "machine",
    "learning", "artificial", "intelligence", "neural", "network",
    "computer", "algorithm", "database", "security", "hello", "world",
    "example", "test", "query", "search", "engine", "information",
    "retrieval", "ranking", "evaluation", "performance", "system",
    "user", "interface", "design", "pattern", "architecture",
]

_PUNCT = list("!@#$%^&*()_+-=[]{};':\",./<>?\\|`~")

_UNICODE_WORDS = [
    "café", "naïve", "München", "Москва", "Ελλάδα", "北京", "こんにちは",
    "안녕하세요", "résumé", "façade", "jalapeño", "über", "señor",
    "😀", "🎉", "🚀", "❤️", "日本", "中国", "España", "Français",
    "Ünïcödé", "test123", "hello_world", "foo_bar",
]

def _gen_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(1, 4)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.3:
            q += "?"
        if rng.random() < 0.2:
            q = q.capitalize()
        lines.append((qid, q))
    return lines

def _gen_medium(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(5, 15)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.5:
            q += rng.choice([".", "?", "!", ","])
        if rng.random() < 0.3:
            pos = rng.randint(0, len(q)-1)
            q = q[:pos] + "," + q[pos:]
        lines.append((qid, q))
    return lines

def _gen_long(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        target_len = rng.randint(500, 3000)
        parts = []
        total = 0
        while total < target_len:
            w = rng.choice(_WORDS)
            parts.append(w)
            total += len(w) + 1
            if rng.random() < 0.1:
                parts.append(rng.choice(_PUNCT))
        q = " ".join(parts)
        lines.append((qid, q))
    return lines

def _gen_punct(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 10)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        chars = list(q)
        for _ in range(rng.randint(5, 20)):
            pos = rng.randint(0, len(chars))
            chars.insert(pos, rng.choice(_PUNCT))
        q = "".join(chars)
        lines.append((qid, q))
    return lines

def _gen_upper(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_WORDS).upper() for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines

def _gen_unicode(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(3, 12)
        words = [rng.choice(_UNICODE_WORDS) for _ in range(k)]
        q = " ".join(words)
        lines.append((qid, q))
    return lines

def _gen_empty_short(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        r = rng.random()
        if r < 0.1:
            q = ""
        elif r < 0.3:
            q = rng.choice([" ", "  ", "   "])
        elif r < 0.5:
            q = rng.choice("abcdefghijklmnopqrstuvwxyz")
        else:
            k = rng.randint(1, 3)
            q = " ".join(rng.choice(_WORDS) for _ in range(k))
        lines.append((qid, q))
    return lines

def _gen_huge(rng, n):
    lines = []
    for i in range(n):
        qid = str(1_000_000 + i)
        k = rng.randint(4, 12)
        words = [rng.choice(_WORDS) for _ in range(k)]
        q = " ".join(words)
        if rng.random() < 0.4:
            q += "?"
        lines.append((qid, q))
    return lines

_WRITE_SPEC = [
    ("short", _gen_short, 20_000, 0),
    ("medium", _gen_medium, 40_000, 1),
    ("long", _gen_long, 5_000, 2),
    ("punct", _gen_punct, 30_000, 3),
    ("upper", _gen_upper, 30_000, 4),
    ("unicode", _gen_unicode, 20_000, 5),
    ("empty-short", _gen_empty_short, 30_000, 6),
    ("huge", _gen_huge, 80_000, 7),
]

_DIRS = {}
for label, gen, n, seed in _WRITE_SPEC:
    d = _BASE / label
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    rng = random.Random(seed)
    lines = gen(rng, n)
    with gzip.open(path, "wt", encoding="utf8") as f:
        for qid, query in lines:
            f.write(f"{qid}\t{query}\n")
    _DIRS[label] = d

_QREL = {str(1_000_000 + i): i % 2 for i in range(1000)}

def _thunk_for(directory, qrel=_QREL):
    def thunk():
        _MOD.download_dir = str(directory)
        return (qrel,)
    return thunk

# Check files
_CHECK_BASE = WORKDIR / "msmarco_queries_checks"

def _make_check_file(name, lines):
    d = _CHECK_BASE / name
    d.mkdir(parents=True, exist_ok=True)
    path = d / "msmarco-doctrain-queries.tsv.gz"
    with gzip.open(path, "wt", encoding="utf8") as f:
        for line in lines:
            f.write(line + "\n")
    return d

_CHECK_DIRS = {
    "empty": _make_check_file("empty", []),
    "one": _make_check_file("one", ["1\thello world"]),
    "malformed": _make_check_file("malformed", ["this is not a tsv line"]),
}

def checks():
    return [
        ("empty-file", _thunk_for(_CHECK_DIRS["empty"])),
        ("one-line", _thunk_for(_CHECK_DIRS["one"])),
        ("malformed", _thunk_for(_CHECK_DIRS["malformed"])),
    ]

def cases():
    return [
        ("short", _thunk_for(_DIRS["short"])),
        ("medium", _thunk_for(_DIRS["medium"])),
        ("long", _thunk_for(_DIRS["long"])),
        ("punct", _thunk_for(_DIRS["punct"])),
        ("upper", _thunk_for(_DIRS["upper"])),
        ("unicode", _thunk_for(_DIRS["unicode"])),
        ("empty-short", _thunk_for(_DIRS["empty-short"])),
        ("huge", _thunk_for(_DIRS["huge"])),
    ]
```

Wait, there's a potential issue: The `_QREL` dict has keys `str(1_000_000 + i)`. The queryids in the files are also `str(1_000_000 + i)`. So qrel keys match some queryids. That's realistic. The function doesn't use qrel, but it's fine.

Now, check the malformed file: `"this is not a tsv line"` has no tab. When read by csv.reader with delimiter="\t", it yields `['this is not a tsv line']`. Then unpacking to `[queryid, query]` raises ValueError. Good.

Now, one more consideration: The function prints "Loading queries..." for every call. In the checks, the malformed case will print then raise. That's fine.

Now, let's think about whether the function might fail on the "one" check file. It has one line "1\thello world". csv.reader yields `['1', 'hello world']`. Unpacks. Then `re.sub` and lower. Returns `{'1': 'hello world'}`. Good.

Now, the empty file: gzip file with no lines. `csv.reader` yields nothing. Returns `{}`. Good.

Now, is there any issue with the file paths? `_DIRS[label]` is a Path. `str(directory)` gives the absolute path if WORKDIR is absolute. WORKDIR is a `pathlib.Path`, likely absolute. So `download_dir` becomes an absolute path. The function does `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")`. That works.

Now, let's verify the import. `importlib.import_module('extract-msmarco')`. This requires that the directory containing `extract-msmarco.py` is on sys.path. The task says to import it as shown, so it should be. Our code does the same.

Now, potential issue: The module name has a hyphen. `importlib.import_module` can handle it because it takes a string. But the module's `__name__` will be 'extract-msmarco'. That's fine.

Now, let's consider the "huge" case output size: 80,000 entries. The dict will have 80,000 keys. The harness compares outputs in full. That's under 100,000. Good.

What about the total memory for all files? 8 gzip files, total uncompressed ~ 255k lines * ~30 chars = ~7.6 MB. Compressed much less. The output dicts during measurement: only one at a time. 80k entries ~ maybe 10 MB. Under 100 MB.

Now, build time: Generating 255k lines and writing gzip. Should be under 10s. Probably ~1-2s.

Now, let's check the "long" case: 5,000 lines, each 500-3000 chars. Total uncompressed ~ 5000 * 1750 = 8.75 MB. Gzip writing 8.75 MB. Fine. The function will read 5,000 lines of long strings. Regex sub on 1750 chars * 5000 = 8.75M chars. That's substantial. Could take ~0.1-0.2s. Good.

Now, let's check the "punct" case: 30,000 lines, each with punctuation. The regex sub will replace many characters. Good.

Now, the "unicode" case: 20,000 lines with unicode. The regex `\w` with Unicode. Python's re module handles Unicode `\w` by default for str patterns. So accented letters, Cyrillic, Chinese are considered word characters and kept. Emojis are not `\w` and replaced with space. That's fine.

Now, let's think about whether the function might fail on unicode input due to encoding. We write with encoding="utf8". The function opens with encoding="utf8". So it's fine.

Now, let's consider the `qrel` argument. The function doesn't use it. The harness will call `load_msmarco_queries(qrel)`. Our thunk returns `(qrel,)`. The `qrel` is `_QREL`, a dict of 1000 entries. That's fine.

But wait: The instructions say "For keyword arguments the thunk returns `call(...)`". Here all arguments are positional. So `(qrel,)` is correct.

Now, let's ensure the thunk does not call the function under test. It doesn't.

Now, let's check if any of the generated query strings could contain a tab or newline. Our `_WORDS` and `_UNICODE_WORDS` and `_PUNCT` don't contain tab or newline. The `rng.choice("abcdefghijklmnopqrstuvwxyz")` returns a single char. The spaces are regular spaces. So no tab/newline.

Now, what about the "empty-short" case with `q = " "` (space)? The line becomes `qid\t \n`. csv.reader will parse as `['qid', ' ']`. Good.

Now, let's consider the possibility that the harness might call the thunk multiple times for the same case. Each call sets the global to the same directory. Fine.

Now, let's consider the possibility that the harness runs the original function and the modified function in separate processes. Then our module-level file creation runs in both processes? Actually, the harness probably runs our code once to generate inputs, then runs the original and modified functions. If it runs in separate processes, our code would run in each process, creating files separately. That's fine, as long as they don't conflict. WORKDIR might be the same, so they might overwrite each other's files. But the content is deterministic, so identical. Fine.

Now, let's double-check the generation functions for any potential index error. In `_gen_medium`, `pos = rng.randint(0, len(q)-1)`. If `len(q)` is 0? q is built from at least 5 words, so len > 0. Fine. In `_gen_punct`, `pos = rng.randint(0, len(chars))`. `len(chars)` can be 0 if q is empty? q is built from at least 3 words, so not empty. Fine.

Now, let's consider the check for `malformed`. The line "this is not a tsv line" has no tab. But csv.reader might treat spaces as part of the field. It yields one field. Unpacking fails. Good.

Now, one more thing: The function `load_msmarco_queries` uses `os.path.join(download_dir, "msmarco-doctrain-queries.tsv.gz")`. If `download_dir` is set to a directory that doesn't exist, it raises FileNotFoundError. Our directories exist. Good.

Now, let's think about the "huge" case: 80,000 lines. The output dict has 80,000 entries. The harness compares the full output. That's a lot of values, but under 100,000. Good.

Now, let's write the final code. I'll include comments for clarity.

But wait: The instructions say "Exactly one ```python block holding the complete source." So we output one code block.

Let's review the code for any syntax errors. We use `_PUNCT = list("!@#$%^&*()_+-=[]{};':\",./<>?\\|`~")`. The string includes a backslash and a backtick. In Python, `\"` is an escaped quote, `\\` is a backslash. That's fine. The list will contain each character.

But wait: The string literal `"!@#$%^&*()_+-=[]{};':\",./<>?\\|`~"` — let's parse it. It starts with `"`, then characters, then `\"` (escaped double quote), then `,./<>?\\|`~`. The `\\` is a literal backslash. The backtick is fine. At the end, `"` closes. So the string is: `!@#$%^&*()_+-=[]{};':",./<>?\|`~`. That's correct. No issues.

Now, let's think about the "unicode" case: We have emojis like "😀". In Python source, these are UTF-8. The file is written with encoding="utf8", so fine. The function reads with encoding="utf8", so fine.

Now, let's consider the size of the `_QREL` dict. 1000 entries. That's fine.

Now, let's ensure that the module `extract-msmarco` is imported before we set its attribute. We do `_MOD = importlib.import_module('extract-msmarco')` at module level. That should work if the path is set. The task says to import it exactly as shown, so the environment supports it.

Now, let's consider if the harness imports the function under test before our code runs. It might do: `load_msmarco_queries = importlib.import_module('extract-msmarco').load_msmarco_queries`. Then it runs our code? Or our code is run first? Typically, they run the candidate's code to define `checks()` and `cases()`, then they import the function. Either way, `sys.modules` has the same module object. Our code imports it and sets the attribute. If the harness imported it first, our import returns the same cached module. We set the attribute. Then the harness calls the function. The function reads the global. So it works.

If the harness imports the function, then runs our code, then the function already holds a reference to the module's globals? The function's global namespace is the module's `__dict__`. So setting `_MOD.download_dir` modifies that `__dict__`. The function will see it. So either order works.

Now, let's test the code mentally for the "empty-short" case. We generate lines with rng. The qid is sequential. Some q are empty. The line is `1000000\t\n`. csv.reader on `1000000\t` yields `['1000000', '']`. Unpacks to queryid='1000000', query=''. Then `re.sub` on '' returns ''. Good.

Now, what about lines with only spaces: `1000001\t \n`. csv.reader yields `['1000001', ' ']`. query=' '. re.sub(r"[^\w ]", " ", " ") -> " ". lower -> " ". Good.

Now, let's consider the "long" case: target_len up to 3000. The while loop builds parts. Each word is added, total increases by len(w)+1. It might overshoot a bit. The resulting q length could be > 3000. That's fine. But we must ensure it doesn't become too large (e.g., > 10000) to avoid memory issues. Max target 3000, each word ~5 chars, so ~500 words. q length ~3000. Fine.

Now, let's check the "punct" case: inserting punctuation into a list of chars. The list length grows. Max initial length ~ 10 words * 6 = 60. Inserting up to 20 chars -> 80. Fine.

Now, let's consider the total build time. Generating 255k lines with random choices and joining. In Python, 255k iterations with several rng calls might take ~0.5-1s. Writing gzip 8 files: gzip compression is fast. Total maybe 1-2s. Under 10s. Fine.

Now, let's think about the output size limit. The "huge" case returns 80,000 entries. The "medium" returns 40,000. The sum of all returned values across all cases is not stored simultaneously. The harness compares each output after each call. But the instruction "keep what it returns ... under about 100 000 values" applies per call. So fine.

Now, let's think about the argument data size limit: "keep each input's data under about 1 000 000 values." Our qrel is 1000 values. The file data is read by the function, not passed as argument. The argument is just qrel. So fine.

Now, let's consider if the function modifies the file? No.

Now, let's consider if the function modifies `download_dir`? No.

Now, let's write the final code. I'll make sure to use the exact function name `load_msmarco_queries`? No, our code defines `checks` and `cases`. The function under test is imported by the harness.

One more detail: The task says "Import it as `load_msmarco_queries = importlib.import_module('extract-msmarco').load_msmarco_queries`". Our code does `_MOD = importlib.import_module('extract-msmarco')`. That's fine.

Now, let's check the thunk for checks: `_thunk_for(_CHECK_DIRS["empty"])`. The `_CHECK_DIRS` dict maps to Path objects. `_thunk_for` takes a directory and returns a thunk that sets `_MOD.download_dir = str(directory)`. For the empty file, it sets to the empty directory. Good.

Now, let's consider the "malformed" check. The thunk sets the global to the malformed directory. The function opens the file, reads the line, csv.reader yields `['this is not a tsv line']`. Then `for [queryid, query] in tsvreader:` tries to unpack. This raises `ValueError: not enough values to unpack (expected 2, got 1)`. The original and modified should both raise. The harness checks identical behaviour (both raise). Good.

Now, could the modified version change the error type? Possibly. But that's what the check is for.

Now, let's write the final code block.

I'll include all imports at the top.

One potential issue: The `WORKDIR` variable is provided by the harness. It's a `pathlib.Path`. We use it directly. It's not defined in our code, as instructed.

Now, let's produce the final answer.