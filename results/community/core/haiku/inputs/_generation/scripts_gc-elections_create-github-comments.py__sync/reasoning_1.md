Let me analyze the function `sync`.

It takes owner, repo, issue_url, voter_comments, file_handles, dryrun.

It calls `gh_run` for non-dryrun, which uses subprocess. That would require `gh` binary. But dryrun=True avoids gh_run... except `post_batches` with dryrun=True just prints. So with dryrun=True, no subprocess calls happen. 

So we can use dryrun=True for all cases, avoiding network/subprocess. But wait — is the function's behavior the same? We're testing energy of the function; using dryrun=True is fine as long as it runs. The task says "A function whose work starts with a request to a server cannot run here" — but with dryrun=True, no requests. So we can run it.

Actually, we should consider: maybe some cases with dryrun=False would call gh_run which needs `gh` on PATH. That would fail. So use dryrun=True only. That's fine.

Now, the function reads module-level things: `MENTION_RE`, `BATCH_SIZE`. We need to import the module. Let's check the module imports: argparse, csv, json, os, re, subprocess, sys. It defines MENTION_RE somewhere. Since we import the module, MENTION_RE is defined at module level. Good.

The function also uses `extract_mentions`, `remove_handle_line`, `post_batches`, `build_body`, `gh_run`. All in the module.

We need to import the module with importlib since filename has dashes.

```python
import importlib
sync_mod = importlib.import_module('create-github-comments')
sync = sync_mod.sync
```

But the import requires the module's directory to be on sys.path. The task says import it as shown. Presumably the test harness sets sys.path appropriately. Let's just do it.

Now, what is MENTION_RE? We don't know its exact pattern but it's likely something like `@([A-Za-z0-9_-]+)`. We need bodies with mentions. Let's construct bodies that contain `* @handle` lines.

Let me think about how the repository builds voter_comments. From `main`, voter_comments come from GitHub API comments filtered by `is_voter_comment` (first line exactly the header). The bodies contain lines like `* @handle` for each voter.

`build_body(handles)` probably builds something like:
```
# Voter notification
* @alice
* @bob
```

And `remove_handle_line` removes a line `* @handle` at start of line.

So voter_comments are dicts with 'id' and 'body'.

Let's design cases.

The function's work:
1. Build file_lower set from file_handles.
2. Extract mentions from all voter comments' bodies, build tagged_lower.
3. For each comment, extract mentions, for each mention not in file_lower, remove handle line, collect removed.
4. Print messages, maybe gh_run (dryrun so no).
5. Post new voters.

So the work is dominated by regex operations over bodies. To make it heavy, we need many comments with many mentions, and many handles.

Let's write a generator for bodies.

MENTION_RE - we need to know what it matches. Let's guess it's `re.compile(r'@([A-Za-z0-9_-]+)')`. Actually let's just use handles that are simple usernames like `user123`. The regex will match @user123.

Let me create a body builder:

```python
def _body(handles):
    lines = ["Voter notification"]
    for h in handles:
        lines.append(f"* @{h}")
    return "\n".join(lines) + "\n"
```

Actually the header must be exact for is_voter_comment but that's not used by sync. sync just processes whatever comments we give.

We need comments with 'id' and 'body'.

Now, `remove_handle_line` removes the line `* @handle` at start of line. So for each stale mention, the body shrinks.

Important: `extract_mentions(new_body)` is called to check if any mentions remain. If none remain, the comment gets deleted (in non-dryrun). In dryrun it just prints.

Now for `total_removed` and `to_add`.

Let's think about scale. We want each call ~1-200ms. Regex over bodies with thousands of mentions should be substantial.

Let's generate, say, 200 comments each with 50 handles → 10,000 mentions. extract_mentions over all bodies: 200*50 = 10k matches. Then per comment, for each mention not in file_lower, remove_handle_line which compiles a regex and does a sub over the body. That's potentially 10k regex compilations and subs. That could be slow — maybe hundreds of ms. Let's tune.

Actually remove_handle_line compiles a regex each call. That's expensive. For 10k stale mentions, 10k compiles + subs. Could be ~100ms+. Let's try smaller.

Let's design 8 diverse cases:

1. Typical: moderate comments, mix of stale and fresh.
2. Many comments, mostly fresh (few removals).
3. Many comments, all stale (all removed).
4. Large single comment with many mentions.
5. Many handles in file_handles, few in comments.
6. Comments with no mentions (empty bodies).
7. Duplicates: same handle repeated.
8. Large scale.

We need the output (prints) to be under 100k values. Prints go to stdout, not returned. The function returns None. So output is None — fine. But "anything it writes" — prints to stdout. Hmm, "keep what it returns (and anything it writes) under about 100 000 values". Prints count as writes. We should keep print volume reasonable. Each comment with removals prints one line. With 200 comments that's 200 lines. Fine.

But in dryrun, for each comment with removals that still has mentions, it prints "--- updated body would be ---" plus the whole body plus blank line. That could be a lot. If we have many such comments with large bodies, output could be large. Let's keep bodies moderate.

Also `post_batches` prints the body of each batch. to_add could be large. build_body of a batch. Let's keep to_add moderate.

Let's be careful: total output should stay under ~100k values. Let's aim for maybe a few thousand lines.

Let me design.

Handles: usernames like `voter_{i}` or realistic `user-{i}`. Let's use `u{i}` maybe. MENTION_RE probably matches word chars. `u123` fine.

Let's define:

```python
import importlib
import random

sync_mod = importlib.import_module('create-github-comments')
sync = sync_mod.sync
```

Wait, the task says import as `sync = importlib.import_module('create-github-comments').sync`. So we do that.

Now build data.

Let me write helper:

```python
def _make_body(handles, header=True):
    lines = []
    if header:
        lines.append("Voter notification")
    for h in handles:
        lines.append(f"* @{h}")
    return "\n".join(lines) + "\n"
```

Comments:

```python
def _make_comment(cid, handles):
    return {'id': cid, 'body': _make_body(handles)}
```

Now cases.

We need fixed seed random.Random(0).

Case 1 "typical": 
- file_handles: 500 handles
- voter_comments: 100 comments, each with 20 handles, mix of handles from file and others.

Let me build a pool.

Let me think about what makes different paths:
- comments with all stale (deleted path) vs partial stale (patch path) vs no stale (continue path).
- to_add: handles in file not tagged.

Let me write a generic builder:

```python
def _gen(n_comments, per_comment, hit_ratio, seed, n_file=1000, dup=1):
    rng = random.Random(seed)
    file_handles = [f"user{i}" for i in range(n_file)]
    file_set = set(file_handles)
    comments = []
    for c in range(n_comments):
        hs = []
        for _ in range(per_comment):
            if rng.random() < hit_ratio:
                hs.append(rng.choice(file_handles))
            else:
                hs.append(f"stale{seed}_{c}_{rng.randrange(10**6)}")
        comments.append({'id': 1000 + c, 'body': _make_body(hs)})
    return file_handles, comments
```

Hmm, but we want diverse. Let's just make several explicit cases.

Concern: remove_handle_line is called for each stale mention. With many stale mentions, this is heavy. Let's estimate: 1 comment with 100 stale mentions → 100 regex compiles+subs over a body of 100 lines. Each sub is O(body length). 100 * 100 lines = 10k line operations. Fine.

For heavy: 200 comments * 50 stale = 10k remove_handle_line calls, each over ~50-line body. That's 10k * 50 = 500k line ops plus 10k regex compiles. Probably ~50-200ms. Let's test mentally... regex compile is ~1-5µs, sub over 50 lines ~10µs. So 10k * 15µs = 150ms. Good.

But we should also keep output manageable: each comment with removals and remaining mentions prints the body. If all 200 comments have partial removals, we print 200 bodies of ~50 lines = 10k lines. That's ~10k "values"? Probably acceptable but let's keep it moderate. Maybe fewer comments.

Actually the print of body only happens when dryrun and there are removals and remaining mentions. Let's control.

Let me design cases more concretely.

Case A "typical-mixed": 50 comments, each 30 handles, 50% stale. file_handles 500. Output ~50 lines + 50 bodies. Hmm.

Actually let's just be reasonable.

Let me consider the constraint "one call takes roughly 1ms to 200ms". Let's aim for a range.

Let me write 8 cases:

1. "small-typical": 20 comments, 10 handles each, 50% stale, file 200 handles.
2. "many-comments-few-stale": 200 comments, 20 handles each, 10% stale.
3. "many-comments-all-stale": 150 comments, 15 handles each, 100% stale.
4. "large-comments": 20 comments, 200 handles each, 50% stale.
5. "no-mentions": 100 comments with bodies without mentions.
6. "duplicates": 50 comments with repeated handles.
7. "big-file-small-comments": file_handles 5000, 100 comments 10 handles each, 20% stale → many to_add.
8. "heavy": 300 comments, 40 handles each, 60% stale.

Wait, for case 7, to_add = file handles not tagged. If file has 5000 and only ~200 tagged, to_add ~4800. post_batches will batch them (BATCH_SIZE unknown, maybe 50). Each batch prints a body. 4800 handles → 96 batches → 96 prints with bodies. Output maybe 4800 lines. OK.

But also building the tagged_lower set requires extracting mentions from all comments.

Hmm, output size: let's keep under 100k values. 4800 lines fine.

Let's also consider: `to_add` computed as list comprehension over file_handles. Fine.

Now checks(): 2-3 small edge inputs.
- empty voter_comments, empty file_handles.
- comment with None body.
- comment with body containing no mentions.

These may raise? None body is handled by `c.get('body') or ''`. Fine.

Let's write checks:

```python
def checks():
    return [
        ("empty", lambda: ("o", "r", "https://x", [], [], True)),
        ("none-body", lambda: ("o", "r", "https://x", [{'id': 1, 'body': None}], [], True)),
        ("no-mentions", lambda: ("o", "r", "https://x", [{'id': 2, 'body': 'hello world'}], ["alice"], True)),
    ]
```

Now cases. Let me write generator functions at module level.

Need to be careful: the function doesn't modify its arguments? Let's check. It iterates voter_comments, reads c.get('body'), c['id']. It builds new_body locally. It doesn't modify comments. file_handles: `to_add = [h for h in file_handles ...]` — doesn't modify. So we can reuse the same data across calls. Good. But to be safe, we can return the same objects. Since no mutation, fine.

But wait: `file_lower = {h.lower() for h in file_handles}` — fine.

Now, one concern: `print` output. The harness compares outputs. Since it's the same every call, fine.

Let's think about MENTION_RE. If it's `@(\w+)` then handles with underscores/digits match. If it's something else... Let's use simple alphanumeric handles to be safe: `user{i}` and `stale{i}`. Actually usernames on GitHub can have hyphens. Let's use alphanumeric only to be safe with any regex.

Actually, what if MENTION_RE requires something specific? Let's think. Common: `re.compile(r'@([A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38})')`. Alphanumeric safe.

Let's use handles like `voter0`, `voter1`, ... and stale ones `stale0`, etc.

Now, one more thing: the body format. remove_handle_line pattern: `^\* @{handle}\s*(?:\n|$)` with MULTILINE|IGNORECASE. So lines must be exactly `* @handle` possibly followed by whitespace. Our body lines `* @handle` match. Good.

But note: after removing a handle line, the mention is gone. Good.

Important subtlety: `extract_mentions` on the body finds all @mentions anywhere, including in the header if it has one. Let's avoid @ in header.

Now let's think about whether the function might call gh_run. Only if dryrun=False. We always pass dryrun=True. Good.

Let me now write the code.

```python
import importlib
import random

sync = importlib.import_module('create-github-comments').sync


def _body(handles):
    return "\n".join(["Voter notification"] + [f"* @{h}" for h in handles]) + "\n"


def _comment(cid, handles):
    return {'id': cid, 'body': _body(handles)}


def _gen(n_comments, per_comment, stale_ratio, seed, n_file, stale_prefix):
    rng = random.Random(seed)
    file_handles = [f"voter{i}" for i in range(n_file)]
    comments = []
    for c in range(n_comments):
        hs = []
        for _ in range(per_comment):
            if rng.random() < stale_ratio:
                hs.append(f"{stale_prefix}{rng.randrange(10**7)}")
            else:
                hs.append(rng.choice(file_handles))
        comments.append(_comment(1000 + c, hs))
    return file_handles, comments
```

Wait: for stale handles, we want them not in file_lower. Using a distinct prefix and large random range ensures not in file. Good.

But there's a subtlety: duplicates. If a stale handle appears in multiple comments, remove_handle_line still works. Fine.

Also, if the same stale handle appears twice in one comment, extract_mentions returns both, and remove_handle_line removes the line first time, second time no-op. That's realistic.

Now cases:

```python
def cases():
    f1, c1 = _gen(30, 12, 0.5, 1, 300, "stalea")
    f2, c2 = _gen(250, 20, 0.08, 2, 800, "staleb")
    f3, c3 = _gen(150, 15, 1.0, 3, 500, "stalec")
    f4, c4 = _gen(15, 250, 0.5, 4, 400, "staled")
    f5, c5 = _gen(120, 0, 0.0, 5, 200, "stalee")   # no handles -> no mentions
    ...
```

Hmm, case 5 with per_comment=0 gives bodies "Voter notification\n" with no mentions. extract_mentions returns []. removed empty, continue. Then to_add = all file handles. post_batches prints. Output large if file big. Keep n_file small, like 200.

Actually with 0 mentions, no removals, so output just "No stale voters to remove" and "Would add 200 new voter(s)" plus batch prints. Fine.

Case 6 duplicates: build manually.

Let me think about case 7: big file, small comments.

Case 8: heavy.

Let me reconsider output sizes. The dryrun patch path prints the full new_body for each comment with removals and remaining mentions. In case 3 (all stale, 100% stale), after removing all mentions, `extract_mentions(new_body)` is empty → delete path, prints one line only, no body. Good, so all-stale is cheap output.

In case 4 (15 comments, 250 handles each, 50% stale), each comment has ~125 stale, ~125 remaining. It prints the body (~125 lines) for each of 15 comments → ~1900 lines. Fine.

In case 1 (30 comments, 12 handles, 50% stale), prints ~30 bodies of ~6 lines. Fine.

Case 8 heavy: 300 comments, 40 handles, 60% stale → 300 bodies of ~16 lines = 4800 lines. Fine.

Case 2: 250 comments, 20 handles, 8% stale → most comments have 0 stale (8% of 20 = 1.6, so ~some have stale). Actually probability at least one stale = 1-0.92^20 ≈ 0.81. So ~200 comments have removals. Each prints body of ~20 lines → 4000 lines. Plus 250 lines. OK.

Hmm, that's a lot of output but within limits.

Actually wait, output size limit "under about 100 000 values". Lines of text... each line is a value? Probably characters or lines. 4000 lines is fine.

Let me also consider to_add output. In cases where file has many handles not tagged, post_batches prints bodies. BATCH_SIZE unknown; if 50, and to_add=800, 16 batches. Each body maybe 50 lines. Fine.

Let me now think about performance. The heavy case: 300 comments * 40 handles = 12000 mentions. extract_mentions called on each body twice (once in tagged_lower loop, once in removal loop) plus once on new_body. So ~36000 mention extractions. Fine.

remove_handle_line called for each stale mention: 300*40*0.6 = 7200 calls, each compiling regex and subbing over a 40-line body. ~7200 * (compile 2µs + sub 10µs) = ~86ms. Good.

Case 4: 15 comments * 250 handles * 0.5 = 1875 stale. Each sub over 250-line body ~50µs → 94ms. Good.

Case 7: big file 5000, 100 comments * 10 handles * 0.2 = 200 stale. Cheap removal. But to_add ~4900, post_batches prints. The list comprehension over 5000 file handles. Cheap. Maybe too cheap (<1ms). Hmm. Let's increase comments. Actually to_add computation is O(n_file). Let's make n_file 20000 and comments 500. Then to_add ~19000. post_batches prints ~380 batches. Output big. Hmm.

Maybe better: make case 7 about large file_handles with many comments. Let's do n_file=10000, n_comments=400, per_comment=15, stale_ratio=0.3. Then tagged ~400*15*0.7=4200 distinct-ish. to_add ~6000. Output: 400 comment lines + bodies + batches. Could be big.

Let's keep it moderate: n_file=3000, n_comments=300, per_comment=12, stale 0.3. to_add ~3000-2500=500-ish. Output manageable.

Hmm, I'm overthinking. Let's just pick reasonable values and ensure correctness.

Actually, an important consideration: the harness runs each case many times. Output is captured. Large output could slow things but fine.

Let me finalize.

Let me also double check: `sync(owner, repo, issue_url, voter_comments, file_handles, dryrun)`. Positional. Thunk returns tuple `(owner, repo, issue_url, voter_comments, file_handles, dryrun)`.

Let me write the final code.

```python
import importlib
import random

sync = importlib.import_module('create-github-comments').sync


def _body(handles):
    lines = ["Voter notification"]
    for h in handles:
        lines.append("* @" + h)
    return "\n".join(lines) + "\n"


def _gen(n_comments, per_comment, stale_ratio, seed, n_file, stale_tag):
    rng = random.Random(seed)
    file_handles = ["voter%d" % i for i in range(n_file)]
    comments = []
    for c in range(n_comments):
        hs = []
        for _ in range(per_comment):
            if rng.random() < stale_ratio:
                hs.append("%s%d" % (stale_tag, rng.randrange(10 ** 7)))
            else:
                hs.append(rng.choice(file_handles))
        comments.append({'id': 100000 + c, 'body': _body(hs)})
    return file_handles, comments
```

Wait, one issue: `rng.choice(file_handles)` picks from the full file list, so tagged handles are in file → not stale. Good.

Now for duplicates case, I'll build manually with a helper.

Let me define cases:

```python
def cases():
    f1, c1 = _gen(30, 12, 0.5, 1, 300, "stalea")
    f2, c2 = _gen(250, 20, 0.08, 2, 800, "staleb")
    f3, c3 = _gen(150, 15, 1.0, 3, 500, "stalec")
    f4, c4 = _gen(15, 250, 0.5, 4, 400, "staled")
    f5, c5 = _gen(120, 0, 0.0, 5, 200, "stalee")
    # duplicates
    rng = random.Random(6)
    f6 = ["voter%d" % i for i in range(400)]
    c6 = []
    for i in range(60):
        hs = [rng.choice(f6) for _ in range(6)] + ["dup%d" % i] * 8 + ["staledup%d" % rng.randrange(1000) for _ in range(4)]
        c6.append({'id': 200000 + i, 'body': _body(hs)})
    f7, c7 = _gen(300, 12, 0.3, 7, 3000, "stalef")
    f8, c8 = _gen(300, 40, 0.6, 8, 1000, "staleg")

    return [
        ("typical-mixed", lambda: ("o", "r", "https://example.com/issues/1", c1, f1, True)),
        ("many-comments-few-stale", lambda: ("o", "r", "https://example.com/issues/2", c2, f2, True)),
        ("all-stale", lambda: ("o", "r", "https://example.com/issues/3", c3, f3, True)),
        ("large-comments", lambda: ("o", "r", "https://example.com/issues/4", c4, f4, True)),
        ("no-mentions", lambda: ("o", "r", "https://example.com/issues/5", c5, f5, True)),
        ("duplicates", lambda: ("o", "r", "https://example.com/issues/6", c6, f6, True)),
        ("big-file", lambda: ("o", "r", "https://example.com/issues/7", c7, f7, True)),
        ("heavy", lambda: ("o", "r", "https://example.com/issues/8", c8, f8, True)),
    ]
```

Wait, case 3 all-stale: handles are all stale, so each comment's mentions all removed → new_body has no mentions → delete path. But wait: the body header "Voter notification" has no mentions. After removing all `* @...` lines, new_body = "Voter notification\n". extract_mentions → empty → delete. Good.

Case 5 no-mentions: c5 bodies have no handles, just "Voter notification\n". No removals. to_add = all 200 file handles. post_batches prints.

Now, the issue: in case 5, per_comment=0 means the loop doesn't run, hs empty. Good.

Duplicates case: hs includes duplicates of "dup%d" 8 times. extract_mentions returns 8 copies. remove_handle_line first removes, rest no-op. removed list has 8 entries. Fine.

Now output volume for case 6: 60 comments, each with some stale (dup and staledup are stale). So each has removals. After removal, remaining mentions include voter handles → patch path, prints body. Body ~18 lines. 60*18 = ~1080 lines. Fine.

Case 2: 250 comments, ~80% have stale, prints body ~20 lines → ~4000 lines. Plus to_add. f2 has 800 handles, tagged distinct maybe ~500. to_add ~300. Fine.

Case 7: 300 comments, 12 handles, 30% stale. ~97% have at least one stale. prints body 12 lines → 3600 lines. to_add ~3000 - tagged. tagged distinct ~300*12*0.7=2520 but many duplicates... n_file 3000, so to_add maybe 1000. Batches. Fine.

Case 8: 300 comments, 40 handles, 60% stale. prints body ~16 lines → 4800 lines. to_add: f8 1000 handles, tagged ~300*40*0.4=4800 draws from 1000 → likely all 1000 covered. to_add ~0. Fine.

Total output per call is fine.

Now performance: case 8 heavy ~7200 remove_handle_line calls. Good.

Let me double-check the "keep each input's data under about 1,000,000 values" — our data is small.

Now, potential issue: does the module import succeed? It imports argparse, csv, json, os, re, subprocess, sys — all stdlib. It defines MENTION_RE and BATCH_SIZE at module level. Import should be fine as long as no side effects. There might be a `if __name__ == '__main__'` guard. Good.

But the import: `importlib.import_module('create-github-comments')` requires the module directory on sys.path. The harness presumably handles that since the task specifies this import. Good.

One more consideration: `MENTION_RE` might match more than we think. If it matches e.g. `@voter0` in "Voter notification"? No @ there. Good.

What about the header "Voter notification" — no @.

Now, does `extract_mentions` return handles without the @? Let's assume yes (findall with group). Then `m.lower() not in file_lower` compares handle to file handles. Good. remove_handle_line uses the handle to build `* @handle`. Good.

If MENTION_RE returns the full match including @, then comparisons would fail. But then the function itself would be broken with the repository's own data. So it must return the handle without @. Good.

Let's also verify: file_handles are like "voter0". In body, "* @voter0". remove_handle_line pattern `^\* @voter0\s*(?:\n|$)`. Matches. Good.

Now checks. Let's make sure they don't raise on original. They should behave identically on both. Fine.

Actually one concern with checks: "empty" with voter_comments=[] and file_handles=[] and dryrun=True. post_batches with empty handles returns early. Prints "No stale voters to remove" and "Would add 0 new voter(s)". Fine.

Now, the thunk for checks returns tuples. Fine.

Let me also consider whether we need `call` for keyword args — no, all positional.

Let me finalize the code. I'll clean it up.

One more: I should ensure module-level data building is under 10s. Our generation is tiny. Good.

Let me write it.

Actually, let me reconsider whether outputs are compared "in full". Since print output goes to stdout, the harness captures it. Same every call. Good.

Let me also double check: in non-dryrun mode gh_run would be called — we never do. Good.

Final code:

```python
import importlib
import random

sync = importlib.import_module('create-github-comments').sync


def _body(handles):
    lines = ["Voter notification"]
    for h in handles:
        lines.append("* @" + h)
    return "\n".join(lines) + "\n"


def _gen(n_comments, per_comment, stale_ratio, seed, n_file, stale_tag):
    rng = random.Random(seed)
    file_handles = ["voter%d" % i for i in range(n_file)]
    comments = []
    for c in range(n_comments):
        hs = []
        for _ in range(per_comment):
            if rng.random() < stale_ratio:
                hs.append("%s%d" % (stale_tag, rng.randrange(10 ** 7)))
            else:
                hs.append(rng.choice(file_handles))
        comments.append({'id': 100000 + c, 'body': _body(hs)})
    return file_handles, comments


def checks():
    return [
        ("empty", lambda: ("o", "r", "https://example.com/issues/0", [], [], True)),
        ("none-body", lambda: ("o", "r", "https://example.com/issues/0",
                               [{'id': 1, 'body': None}], [], True)),
        ("no-mentions", lambda: ("o", "r", "https://example.com/issues/0",
                                 [{'id': 2, 'body': "just a normal comment"}],
                                 ["alice"], True)),
    ]


def cases():
    f1, c1 = _gen(30, 12, 0.5, 1, 300, "stalea")
    f2, c2 = _gen(250, 20, 0.08, 2, 800, "staleb")
    f3, c3 = _gen(150, 15, 1.0, 3, 500, "stalec")
    f4, c4 = _gen(15, 250, 0.5, 4, 400, "staled")
    f5, c5 = _gen(120, 0, 0.0, 5, 200, "stalee")

    rng = random.Random(6)
    f6 = ["voter%d" % i for i in range(400)]
    c6 = []
    for i in range(60):
        hs = ([rng.choice(f6) for _ in range(6)]
              + ["dup%d" % i] * 8
              + ["staledup%d" % rng.randrange(1000) for _ in range(4)])
        c6.append({'id': 200000 + i, 'body': _body(hs)})

    f7, c7 = _gen(300, 12, 0.3, 7, 3000, "stalef")
    f8, c8 = _gen(300, 40, 0.6, 8, 1000, "staleg")

    return [
        ("typical-mixed", lambda: ("o", "r", "https://example.com/issues/1", c1, f1, True)),
        ("many-comments-few-stale", lambda: ("o", "r", "https://example.com/issues/2", c2, f2, True)),
        ("all-stale", lambda: ("o", "r", "https://example.com/issues/3", c3, f3, True)),
        ("large-comments", lambda: ("o", "r", "https://example.com/issues/4", c4, f4, True)),
        ("no-mentions", lambda: ("o", "r", "https://example.com/issues/5", c5, f5, True)),
        ("duplicates", lambda: ("o", "r", "https://example.com/issues/6", c6, f6, True)),
        ("big-file", lambda: ("o", "r", "https://example.com/issues/7", c7, f7, True)),
        ("heavy", lambda: ("o", "r", "https://example.com/issues/8", c8, f8, True)),
    ]
```

Wait, there's a subtle issue with the "all-stale" case and the delete path: it prints one line per comment, fine. But total_removed > 0 → prints total. Good.

Another subtlety: in case 3, all handles stale, but some might coincide? stale_tag "stalec" + random 0..10^7. n=150*15=2250 draws, collisions unlikely. Fine.

I think this is good. Let me double check the thunk returns exactly what sync expects: owner, repo, issue_url, voter_comments, file_handles, dryrun. Yes.

One thing: the function signature order is (owner, repo, issue_url, voter_comments, file_handles, dryrun). Yes.

I'm fairly confident. Let me also consider: could MENTION_RE match something in "Voter notification"? No @.

Could the stale handle strings contain characters that break the regex in remove_handle_line? `re.escape(handle)` — safe.

Alright.

Actually, one concern: what if MENTION_RE is defined such that it matches `@` followed by word chars, and our handles like "voter0" are fine. Yes.

Let me reconsider the possibility that the harness's output comparison includes stdout. If prints are huge, comparison is slow but fine.

I'll go with this.

Wait, one more: the instructions say "We run them on the original function and keep the 4 that do the most work." So 8 cases, 4 kept. Our cases should be diverse. Good.

Let me finalize.