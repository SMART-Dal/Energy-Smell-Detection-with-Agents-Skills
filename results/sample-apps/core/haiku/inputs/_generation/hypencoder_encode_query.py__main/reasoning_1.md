Let me analyze this function. It's a CLI main function that parses args from sys.argv, reads a tokenizer file, encodes a query, and dumps JSON to stdout.

Key issues:
1. It uses `argparse.ArgumentParser().parse_args()` which reads `sys.argv` — not the passed argument. So we need to set `sys.argv` in the thunk. But wait — the thunk returns arguments for the function. `main()` takes no arguments. So the thunk must set `sys.argv` and then... but the thunk returns the args tuple. The setup (setting sys.argv) can happen in the thunk, but the thunk returns `()`.

Wait but the timing: "Thunks run before the timing starts; only the call of the function is timed." So the thunk can set `sys.argv` and return `()`.

Hmm, but sys.argv is global state. Setting it in the thunk is fine.

2. It writes to `sys.stdout` via `json.dump`. We need to redirect sys.stdout to something (e.g., io.StringIO or a file under WORKDIR). But wait, redirecting sys.stdout... is that "faking the environment"? Hmm. It's data setup. Actually, we could set `sys.stdout` to an open file under WORKDIR. But then json.dump writes to it. The output is compared in full — "keep what it returns (and anything it writes) under about 100 000 values". Hmm, the output is written to stdout, not returned. How does the harness compare? It says "the function's output is compared in full after every input". Since main returns None, output must be captured somehow. Maybe the harness captures stdout. Hmm.

Actually, if the harness captures stdout normally, we might not need to redirect. But to be safe... Hmm. Actually, redirecting sys.stdout to a StringIO would be setting data. But is it needed? If the harness captures stdout, then json.dump writes there and it's compared. If we redirect, the harness wouldn't see it.

Let me think: main() returns None always. So output comparison would be based on side effects. The most natural side effect is stdout. The harness likely captures stdout. So we should NOT redirect stdout — let it write to the real stdout, which the harness captures.

But wait, there's a problem: if we don't redirect, each call writes JSON to stdout. That's fine.

Hmm, but actually the instructions say "Anything the function writes must go under WORKDIR too." That suggests we should redirect stdout to a file under WORKDIR. But then comparison of output... Hmm.

Actually, re-reading: "Files: if the function reads files, create them under WORKDIR... Anything the function writes must go under WORKDIR too."

So we should redirect sys.stdout to a file under WORKDIR. Then the harness can compare the file contents? Or maybe the harness compares the return value only.

Hmm, this is ambiguous. Let me think about what's safest. If main writes to real stdout and the harness captures it, comparison works. If we redirect to a file, the harness might compare the file... but it says "the function's output is compared in full after every input". 

Actually, since main() returns None, and the only observable output is stdout, the harness must be capturing stdout. Let me just let it write to stdout naturally. Actually wait — but then "anything it writes must go under WORKDIR" wouldn't apply.

Hmm. Let me reconsider. Perhaps the safest is to redirect sys.stdout to a file under WORKDIR, and the harness... no.

Actually, I think the harness likely captures stdout/stderr during the call. Let me not redirect. Actually, hmm, but the concern is that writing to stdout many times is fine.

Let me think about it differently: the task says the output is compared in full. For a function returning None, the comparison must be of captured stdout. So the harness captures stdout. Therefore we should leave stdout alone.

But there's a risk: if the harness doesn't capture stdout, the output comparison is trivially equal (both None), and energy is what matters. Either way, leaving stdout alone is safe.

Actually wait, there's another consideration: if we redirect stdout to a file, the file must be reset each call (truncate). The instructions say "If it creates files, have the thunk remove them first." So the thunk would truncate the file. That's doable.

Hmm, I'll go with redirecting sys.stdout to a StringIO... no. Let me think about which is more likely correct.

Given the phrasing "Anything the function writes must go under WORKDIR too", I think they want us to redirect stdout to a file. But then how is output compared? Maybe the harness compares the file after the call. Hmm.

Actually, maybe the harness captures stdout itself by replacing sys.stdout, and if we replace it in the thunk, we override. That would break comparison.

I think the safest is: don't touch sys.stdout, let the harness handle it. Because the harness's job is to capture output. If it doesn't capture, no harm.

Hmm, but actually, if the harness captures stdout, and we run the function many times, each writing ~64 floats JSON... fine.

Wait, but there's a subtlety: if the harness captures stdout, does it capture during the timed region? Probably yes.

OK let me just not redirect. Actually, hold on. Let me reconsider once more. The instructions explicitly mention writing files under WORKDIR. This might be a generic instruction. For this function, the natural output is stdout. I'll leave stdout alone.

Hmm, but actually there's a real risk that the harness does NOT capture stdout and the massive output floods the terminal... but that's the harness's problem.

Let me reconsider: maybe I should redirect to a file to be safe about output comparison. But if the harness captures stdout, then redirecting means both original and modified write to the same file... no, each call truncates.

Ugh. Let me just go with a StringIO-like approach? No.

Decision: I'll redirect sys.stdout to a file under WORKDIR, and truncate it in the thunk. Wait, but then the "output compared in full" — the harness would compare the return value which is None for both. Hmm, that makes comparison trivial and the energy measurement is the point.

Actually, you know what, I bet the harness captures stdout because that's the only meaningful output. Let me NOT redirect. If the harness doesn't capture, we get lots of stdout but that's fine.

Hmm, wait. Actually, there's a strong argument: many of these tasks have functions that print. The harness surely captures stdout to compare. Let me go with not redirecting.

Hmm, but actually... let me reconsider. If the harness captures stdout via contextlib.redirect_stdout, it replaces sys.stdout during the call. Our thunk setting sys.argv is fine. So we don't need to do anything about stdout.

OK. Now the bigger issue: the tokenizer file.

`Tokenizer.from_file(args.tokenizer)` — needs a real tokenizer.json file. We must create it under WORKDIR. But we can't download one. Can we create a valid tokenizer.json from scratch? The `tokenizers` library is available (it's imported). We can build a tokenizer in Python using `Tokenizer` and save it to a file with `tok.save(path)`.

Yes! `from tokenizers import Tokenizer` and build a tokenizer programmatically, then `tok.save(str(path))`. That creates a real tokenizer.json.

We need a tokenizer that has a `[PAD]` token and can encode text. Let's build a BPE or WordLevel tokenizer.

Simplest: use `tokenizers.models.WordLevel` with a vocab, and a pre-tokenizer like Whitespace. Then `Tokenizer(model)`. Set `tokenizer.pre_tokenizer = Whitespace()`. Save.

But we need `tok.token_to_id(PAD_TOKEN)` to return non-None, so include "[PAD]" in vocab.

Also `tok.enable_truncation(max_length=64)` and `enable_padding(length=64, pad_id=..., pad_token="[PAD]")`. These should work with a WordLevel model.

Encoding a query: WordLevel with Whitespace pretokenizer — unknown words... WordLevel by default maps unknown to unk_token. If unk_token is not set, it might raise. Let's set unk_token="[UNK]" and include it in vocab.

Actually, let's use a BPE model? WordLevel is simpler.

Let me write:

```python
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

vocab = {"[PAD]": 0, "[UNK]": 1}
# add words
for i in range(1000):
    vocab[f"w{i}"] = len(vocab)
tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
tok.pre_tokenizer = Whitespace()
tok.save(str(TOKENIZER_PATH))
```

Hmm, but is `tokenizers.pre_tokenizers.Whitespace` available? Yes, standard.

Actually, maybe use `tokenizers.pre_tokenizers.BertPreTokenizer` or just Whitespace. Whitespace is fine.

Wait, but with padding enabled and max_length 64, encoding a short query gives 64 ids. Good.

Now, the function reads `args.tokenizer` default "app/models/tokenizer.json", but we pass `--tokenizer <path>`.

Now sys.argv: `parse_args()` reads sys.argv[1:]. So set `sys.argv = ["encode_query.py", query, "--tokenizer", str(TOKENIZER_PATH), ...]`.

Now modes: default (hypencoder_onnx), --rerank, --cosine, --lexical. The --cosine path skips the tokenizer entirely (no Tokenizer.from_file). That's a different code path — good for diversity.

Now, each thunk must set sys.argv and return (). But the thunk runs before timing; setting sys.argv is part of setup. Good.

But wait: "Same work on every call". Setting sys.argv in the thunk each time is fine.

Now let's design 8 cases:
1. Default mode (hypencoder_onnx), short query.
2. Default mode, long query (truncation exercised).
3. --rerank with medium query.
4. --lexical with query.
5. --cosine with query (no tokenizer).
6. --rerank with long query.
7. --hits large.
8. --lexical with unicode / weird query.

Hmm, but the work is dominated by tokenization. Tokenizing a query is fast (microseconds to ms). The instruction says one call should take roughly 1ms to 200ms. Tokenizing a short query might be < 1ms. Hmm.

Well, `Tokenizer.from_file` loads the file each call — that's disk I/O and parsing, maybe ~1ms. That might be the dominant cost. Actually loading a tokenizer.json with 1000 vocab entries is fast.

To make it heavier, we can make the vocab larger (e.g., 50,000 words) so loading the tokenizer takes longer. And the query longer.

But careful: `tok.save` with 50k vocab — fine.

Hmm, but the file is read each call (from_file). With a 50k vocab, the JSON file is maybe 1-2 MB. Parsing that each call... maybe a few ms. Good.

Also `np.array(enc.ids, dtype=np.float32).tolist()` — cheap.

Let's make the tokenizer vocab sizable: 30,000 words. And queries of varying length.

Actually, let me reconsider: the main cost is `Tokenizer.from_file`. Let's make the file reasonably large. 30k vocab BPE-ish... WordLevel vocab JSON is like `{"w0": 0, ...}` — 30k entries, ~500KB. Fine.

Let me also consider making the query long (many words) so encoding does more work — but truncation at 64 limits it. Actually truncation happens after encoding, so encoding still processes all tokens. With Whitespace pretokenizer and WordLevel, encoding 10,000 words is work. But the query string is passed as one argv element; that's fine.

Hmm, but the query is also put into body["q"] for rerank/lexical. And for default mode, only the encoded ids go in. The output size: 64 floats × 2 = 128 values. Fine.

Let me make queries of varying lengths: short (5 words), medium (100 words), long (5000 words).

Wait — but for the default (onnx) mode, body["q"] is not set. So query length doesn't affect output size. Good.

For rerank/lexical, body["q"] = full query string. If query is 5000 words, the output JSON includes the whole query. That's ~1 value. Fine.

OK. Now about the `--cosine` mode: it doesn't load the tokenizer, so it's much faster. Maybe < 1ms. Hmm. But it's a distinct code path. Include it anyway.

Let me now think about timing. Actually the instruction says "One call should take roughly 1 ms to 200 ms". If some are faster, they get dropped by the "keep the 4 that do the most work" rule. That's fine — we provide 8, they keep 4.

Now, checks(): 2-3 small edge inputs, may raise.
- Empty query: `main` with query "" — tokenizing empty string. Might work or raise.
- Query with unknown tokens.
- Missing tokenizer file → sys.exit (raises SystemExit).

Hmm, but checks are "checked only for identical behaviour, never measured". They may raise. Let's include:
1. Empty query string.
2. Query that's pure whitespace / special chars.
3. --cosine with empty query.

Actually, careful: checks that call sys.exit would raise SystemExit — that's allowed ("These may raise"). But maybe better to keep them simple.

Let me write checks:
- ("empty-query", thunk setting sys.argv with query "")
- ("single-char", query "a")
- ("cosine-empty", --cosine with "")

Now, one concern: sys.exit on missing tokenizer. Not needed.

Another concern: `json.dump(body, sys.stdout)` — writing to stdout. Each call writes. Fine.

Now, about redirecting stdout. Let me reconsider one more time... 

Actually, I realize there might be an issue: if the harness captures stdout and compares, and both original and modified produce the same JSON, good. If we redirect to a file, the harness sees nothing. I'll not redirect.

Hmm, but wait — actually, I worry the harness might not capture stdout and instead the output comparison is on the return value (None). Then it doesn't matter. Either way, not redirecting is safe.

Hmm, but there's a subtle issue: if we don't redirect and the harness doesn't capture, running the function 1000s of times floods stdout. But that's the harness's design.

Actually, let me reconsider the instruction: "keep what it returns (and anything it writes) under about 100 000 values". For default mode, it writes ~130 numbers. Fine.

OK, decision: don't redirect stdout. Actually... hmm, let me reconsider. If the harness captures stdout via redirect_stdout, then the function writes to the captured buffer. Good. If the harness doesn't, output goes to terminal. Not our problem.

Alright.

Wait, actually — there's a real concern. The instructions say "Anything the function writes must go under WORKDIR too." This strongly implies they want us to redirect stdout to a file under WORKDIR. And then presumably the harness compares... hmm, but it can't compare a file we manage.

Hmm, maybe the harness compares stdout AND the file? Unclear.

Let me think about it from the perspective of: what would break? If the harness captures stdout: not redirecting → works. Redirecting → harness sees empty output, comparison passes trivially (both empty), energy measured. Also works but loses output comparison.

If the harness doesn't capture stdout: not redirecting → output floods. Redirecting → clean.

Hmm. Risk assessment: The instruction about WORKDIR files is generic boilerplate. The phrase "anything it writes" — for a function that writes to stdout, the harness surely captures stdout.

I'll go with redirecting sys.stdout to a file under WORKDIR. Wait no...

Ugh, let me just decide based on: the harness compares "the function's output in full". For main(), output = stdout. The harness must capture it. So I should NOT interfere with stdout. 

Final: don't redirect.

Hmm, actually hold on. Let me reconsider. If the harness replaces sys.stdout with its capture buffer before calling, and our thunk also sets sys.stdout... order matters. The thunk runs before timing, harness capture is set up around the timed call. So harness wins. Fine.

OK, not redirecting.

Now, another thought: maybe I should redirect to a file to avoid the harness's stdout capture being slow (writing to a pipe/terminal is slow). But that's the harness's concern.

Alright, let me also consider: is there a risk that writing to real stdout during the timing makes the timing dominated by I/O? Possibly. But for the original vs modified comparison it's the same. Fine.

Hmm, actually, you know, let me redirect to a file under WORKDIR. Reason: it makes the measurement cleaner and satisfies the WORKDIR instruction. And if the harness captures stdout, it just sees nothing extra. But then output comparison is trivial...

Argh. Let me think about which produces a valid experiment. The key requirement: "Every case must run to completion on the original function without raising." Both approaches satisfy that.

I'll go with NOT redirecting, trusting the harness captures stdout. This preserves output comparison.

Hmm, wait. Actually, let me reconsider by thinking about what "output" means. If the harness didn't capture stdout, then for main() the output is None and there'd be nothing to compare — the task would be pointless. So the harness captures stdout. Confirmed. Don't redirect.

OK now let's write the code.

```python
import os
import random
import sys
from pathlib import Path

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

import encode_query  # not needed actually
```

Wait, the task says import as `from encode_query import main`. But we don't call main in our code — the harness does. We just need to set up. Actually we might not need to import main at all. But the instructions say "Import the repository's modules exactly as shown in the task." Hmm, it says import exactly as shown. We probably don't need it. But maybe we do need `encode_query` module for globals? The function reads MAX_SEQ and PAD_TOKEN from its module. We don't need to change them.

Actually, we might not need to import it. But let's import it to be safe? No, unnecessary imports could be fine. Let me not import main since we don't use it. Hmm, but the example imports `from search.index import Index` because it uses Index. Here we don't use main. So no import needed.

Actually, we don't call main. The thunk returns `()` and the harness calls `main()`. So we don't need to import it. But it doesn't hurt. I'll skip it.

Hmm, actually wait. Do we need `import encode_query` to ensure the module is loaded? The harness does `from encode_query import main`. Fine.

Now building the tokenizer file:

```python
_BASE = WORKDIR / "tokenizer.json"  # hmm, default path is app/models/tokenizer.json
```

Actually, we pass --tokenizer explicitly, so path can be anywhere under WORKDIR.

Let's build:

```python
def _build_tokenizer(path, n_words, seed):
    rng = random.Random(seed)
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i in range(n_words):
        vocab[f"tok{i}"] = len(vocab)
    tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    tok.save(str(path))
```

Hmm, but we want queries to actually hit known tokens sometimes. Let's use words like "tok123". Queries generated from the vocab.

Actually, since unknown words map to [UNK], it works either way. But let's make queries use real tokens for realism.

Let me generate queries:

```python
def _query(n_words, seed, vocab_size):
    rng = random.Random(seed)
    return " ".join(f"tok{rng.randrange(vocab_size)}" for _ in range(n_words))
```

But wait — the query string is also written into the JSON for rerank/lexical. That's fine.

Hmm, but for a 5000-word query, the string is ~30KB, written into JSON. Output size ~30KB — under 100k values? It's one string value. Fine.

Now, the tokenizer.json file: with WordLevel and 30000 vocab, the JSON is `{"version":"1.0","truncation":null,"padding":null,"added_tokens":[],"normalizer":null,"pre_tokenizer":{"type":"Whitespace"},...}` plus the vocab. Actually the vocab is stored under model. Size maybe 500KB. Loading it each call: `Tokenizer.from_file` parses JSON. ~1-5 ms. Good.

Let me make vocab 50000 to be safe for timing.

Hmm, but "building all inputs under about 10 s" — building the tokenizer file once at module level is fine.

Wait, but we need multiple tokenizer files? No, one file, different queries and modes.

Hmm, but different cases should do "different work". Loading the same file each time is the same work. To vary, we could use different tokenizer files with different sizes. Let's create 2-3 tokenizer files of different sizes. Actually, let's create a couple: small (5k), large (60k). Different loading cost.

Actually, simpler: one big tokenizer file, vary the query and mode. The mode variation gives different code paths.

Let me create 2 tokenizer files: one with 8000 words, one with 60000 words. Hmm, but the vocab words must match the queries. Let's just use one vocab of 60000 and generate queries from it.

Hmm, but then all cases load the same file. That's fine — the "different work" is in query length and mode.

Actually, to add diversity, let me create a second tokenizer file with a different pre-tokenizer (e.g., BertPreTokenizer) and different vocab. Eh, keep it simple.

Let me just do one tokenizer file with 60000 vocab.

Hmm, wait: `tok.save` for 60000 vocab — the JSON dump is fine.

Now, timing check: is `Tokenizer.from_file` on 60000-vocab file fast enough? Probably ~5-10ms. Good, within 1-200ms.

Encoding a long query (50000 words) with Whitespace + WordLevel: 50000 lookups, maybe 20-50ms. Good.

Let's design cases:

1. "default-short": default mode, query 8 words, tokenizer big.
2. "default-long": default mode, query 20000 words (heavy encode).
3. "rerank-medium": --rerank, query 500 words.
4. "lexical-medium": --lexical, query 500 words.
5. "cosine": --cosine, query 100 words (no tokenizer load).
6. "rerank-huge": --rerank, query 30000 words.
7. "default-hits100": default, --hits 100, query 1000 words.
8. "lexical-long": --lexical, query 10000 words + unicode words.

Hmm, cosine mode does very little work (just builds a dict and json.dump). Might be <1ms. It'll be dropped. Fine.

Now, sys.argv setting in thunk:

```python
def _argv(query, tokenizer, extra):
    return ["encode_query.py", query, "--tokenizer", str(tokenizer)] + extra
```

And thunk:
```python
lambda: (sys.argv.__setitem__(slice(None), argv), ())[1]
```
That's ugly. Better:

```python
def _set_argv(argv):
    sys.argv = argv
    return ()
```

But the thunk must return the args tuple. So:

```python
lambda: (_set_argv(argv),)[0]  # returns ()
```

Hmm, `_set_argv` returns `()`. So `lambda: _set_argv(argv)` returns `()`. 

Wait, but the thunk returns the arguments for the function. main takes no args. So return `()`. And `_set_argv` returns `()` after setting sys.argv. 

But careful: `sys.argv = argv` inside a function creates a local... no, `sys.argv = argv` assigns to the module attribute of sys. That's fine — it's not a local variable since we're not declaring it. Actually `sys.argv = argv` sets the attribute on the sys module. Yes, that works globally.

Good.

Now, the thunk is called before timing. The harness calls `main()` with the returned args `()`. Good.

Let me write:

```python
def _setup(argv):
    sys.argv = list(argv)
    return ()
```

Then cases use `lambda: _setup(_argv(...))`.

Now, checks:

```python
def checks():
    return [
        ("empty-query", lambda: _setup(["encode_query.py", "", "--tokenizer", str(TOK)])),
        ("single-token", lambda: _setup(["encode_query.py", "tok0", "--tokenizer", str(TOK)])),
        ("cosine-empty", lambda: _setup(["encode_query.py", "", "--cosine"])),
    ]
```

Hmm, for cosine, no --tokenizer needed (it's ignored). Fine.

Wait, for checks, "checked only for identical behaviour, never measured. These may raise." So if empty query raises, that's fine as long as both original and modified raise identically.

Actually, empty query with Whitespace pretokenizer: encodes to empty list. Then padding to 64 with pad_id. Should work. Actually, does padding work with 0 tokens? `enable_padding(length=64)` pads to 64. Should be fine.

Hmm, but truncation max_length=64 also. Fine.

Now, one more concern: `main()` calls `sys.exit(...)` only if pad_id is None. Our vocab has [PAD], so fine.

Now let me double check the WordLevel model API: `WordLevel(vocab, unk_token=None)`. In recent tokenizers versions, `WordLevel(vocab=None, unk_token=None)`. Yes.

`Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))`. Good.

`tok.pre_tokenizer = Whitespace()`. Good.

`tok.save(path)`. Good.

Now, does `enable_padding(length=MAX_SEQ, pad_id=pad_id, pad_token=PAD_TOKEN)` work? Yes.

But note: after `enable_padding`, encoding returns exactly 64 ids. And `enable_truncation(max_length=64)`. Order: truncation then padding. Fine.

Now, one issue: with padding enabled, `enc.ids` has length 64 always. And `enc.attention_mask` too. Good.

Now, the query for the long case: 20000 words. Encoding: Whitespace splits into 20000 tokens, each looked up. Then truncation to 64. Fine.

But the query string is ~20000*5 = 100KB. For default mode, it's not included in the body. For rerank/lexical it is. Let's keep long queries only for default mode to avoid huge JSON... actually 100KB JSON is fine.

Hmm, "keep what it returns (and anything it writes) under about 100 000 values" — a 100KB string is 1 value. Fine.

Now let's think about whether the harness renders arguments before/after each call. "Its arguments are rendered before and after each call to see whether it changed them". main takes no arguments, so nothing to render. Good — sys.argv isn't an argument.

Wait, but sys.argv is global state that changes... but it's set in the thunk, not by main. main doesn't modify sys.argv. Fine.

Now, `json.dump(body, sys.stdout)` — writes to stdout. If the harness captures stdout, fine.

Hmm, one more: the harness might run each case many times. Each call loads the tokenizer file. Fine.

Let me now also consider: should the tokenizer file be created at module level? Yes, since building it takes time (60k vocab). Module-level code runs once.

But WORKDIR is provided. Module-level code can use it.

Let me write the final code.

```python
import random
import sys

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

_VOCAB_SIZE = 60000
_TOKENIZER = WORKDIR / "tokenizer.json"


def _build_tokenizer(path, vocab_size):
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i in range(vocab_size):
        vocab[f"tok{i}"] = len(vocab)
    tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    tok.save(str(path))


_build_tokenizer(_TOKENIZER, _VOCAB_SIZE)


def _query(n_words, seed):
    rng = random.Random(seed)
    return " ".join(f"tok{rng.randrange(_VOCAB_SIZE)}" for _ in range(n_words))


def _setup(argv):
    sys.argv = list(argv)
    return ()


def _argv(query, extra=()):
    return ["encode_query.py", query, "--tokenizer", str(_TOKENIZER)] + list(extra)
```

Wait, but for cosine, --tokenizer is irrelevant but harmless. Actually --tokenizer is a valid arg for all modes. So always include it. Good, simpler.

Hmm, but the cosine path doesn't use it. Fine.

Now cases:

```python
def cases():
    q_short = _query(8, 0)
    q_med = _query(500, 1)
    q_long = _query(20000, 2)
    q_huge = _query(30000, 3)
    q_mix = _query(1000, 4)
    ...
    return [
        ("default-short", lambda: _setup(_argv(q_short))),
        ("default-long", lambda: _setup(_argv(q_long))),
        ("default-hits100", lambda: _setup(_argv(q_mix, ["--hits", "100"]))),
        ("rerank-medium", lambda: _setup(_argv(q_med, ["--rerank"]))),
        ("rerank-huge", lambda: _setup(_argv(q_huge, ["--rerank"]))),
        ("lexical-medium", lambda: _setup(_argv(q_med, ["--lexical"]))),
        ("lexical-long", lambda: _setup(_argv(q_long, ["--lexical"]))),
        ("cosine", lambda: _setup(_argv(q_med, ["--cosine"]))),
    ]
```

That's 8.

Hmm, the queries are built at module... no, inside cases(). cases() is called once before timing presumably. Building 30000-word strings is fast.

Wait — "Generate stressful inputs: ... different paths through its code, sizes, data distributions". Good.

But note: all queries use tokens from the same vocab, so encoding is all hits. Add a case with unknown tokens? Let's make one query with some unknown words. E.g., q_mix includes some "unk_xyz" words. Actually [UNK] handling. Let's add.

Let me make q_mix = mix of known and unknown.

Actually, let me reconsider the "different work" aspect. The main cost is tokenizer loading (same for all tokenizer-using cases) + encoding (varies with query length). The cosine case has no tokenizer load.

Hmm, to add more diversity, maybe use a second smaller tokenizer file. Let's do that: create a small tokenizer (8000 vocab) and a large one (60000). Cases vary which file.

But then queries must use tokens from the respective vocab. Let's handle: small vocab tokens "stok{i}", large "ltok{i}".

Hmm, this adds complexity. Let me think if it's worth it. The loading cost differs, giving different work. I think it's a nice touch but maybe overkill. Let me include it — it's not much code.

Actually, let's keep it simpler with one tokenizer but vary query length a lot. The encoding cost varies from ~0 to ~50ms. The load cost is constant ~5ms. So total varies from 5ms to 55ms. That's a reasonable range.

Hmm, but the "keep the 4 that do the most work" — the top 4 would be the longest queries. Fine.

Actually, let me add a second tokenizer to diversify loading cost. It's easy:

```python
_TOKENIZER_SMALL = WORKDIR / "tokenizer_small.json"
_build_tokenizer(_TOKENIZER_SMALL, 5000)
```

But then queries must use the right vocab. Let me just make the small tokenizer's vocab a subset... eh, actually unknown tokens map to [UNK] anyway, so any query works with any tokenizer. So I can use the same queries with either tokenizer. 

So: make queries from the large vocab; using them with the small tokenizer just produces more UNKs. Fine.

Let me do that: two tokenizer files, one small (5k), one large (60k).

Hmm, but then `_argv` needs a tokenizer param.

```python
def _argv(query, tokenizer, extra=()):
    return ["encode_query.py", query, "--tokenizer", str(tokenizer)] + list(extra)
```

OK.

Let me finalize.

Actually, one concern about `Whitespace` pretokenizer with empty string: it produces no tokens. Then padding to 64. Should be fine.

Another concern: does `tok.save` require the directory to exist? WORKDIR exists. Good.

Let me also double check `Tokenizer.from_file` accepts a str path. Yes.

Now about the timing: `Tokenizer.from_file` on a 60k vocab file. Let's estimate: JSON with 60k keys, ~1MB. Parsing ~10ms. Plus building the model. Fine.

Let's write it.

One more thought on stdout: I decided not to redirect. But let me reconsider "Anything the function writes must go under WORKDIR too." If the harness doesn't capture stdout, then the function writes to the terminal — violating the instruction. Hmm.

You know what, let me redirect sys.stdout to a file under WORKDIR, and truncate it in the thunk. This satisfies the instruction. The output comparison would then be... hmm.

Actually, here's a thought: maybe the harness captures stdout by default, and if we redirect, it can't compare. But the harness says "the function's output is compared in full". For main(), if we redirect stdout to a file, the harness can't see the output.

Hmm, but maybe the harness compares the file? Unlikely.

OK here's my final reasoning: The harness almost certainly captures stdout (that's how it compares output for printing functions). The WORKDIR instruction is generic boilerplate. I'll leave stdout alone.

Hmm, but wait. Let me reconsider: what if the harness does NOT capture stdout, and instead relies on us redirecting? Then output comparison is on return value (None) and both match. Energy is measured. That works too.

Either way, not redirecting works for the experiment (both original and modified behave the same). The only risk is flooding. I'll accept it.

Hmm, actually, no. Let me reconsider once more. If the harness doesn't capture stdout, then running main() 1000 times per case × 8 cases × 2 versions = 16000 JSON dumps to the terminal. That could be slow but not fatal. And it would be the same for both versions.

But actually, if it's writing to a terminal, that I/O dominates the timing, making the measurement meaningless. Hmm. That's a real concern.

If the harness captures stdout into a StringIO, the write is cheap.

I think the harness captures. Most such harnesses do.

Hmm, let me hedge: I could redirect sys.stdout to a file under WORKDIR in the thunk. Then:
- If harness captures stdout: it captures nothing (we replaced sys.stdout), output comparison trivial. Energy measurement clean.
- If harness doesn't capture: clean, no flooding.

But then output comparison is lost. Hmm.

Alternatively: don't redirect, trust the harness.

I'll go with not redirecting. It's the most faithful.

Hmm, hmm. Actually, let me reconsider the exact wording: "the function's output is compared in full after every input". And "Its arguments are rendered before and after each call". For a function with no args and no return, the only output is stdout. So the harness MUST capture stdout. Confirmed. Don't redirect.

Final answer.

Wait, one more thing: `json.dump(body, sys.stdout)` — if the harness replaces sys.stdout with a capture object, json.dump works with any object having write(). Good.

Now let me also make sure the module-level tokenizer building doesn't take too long. 60k vocab dict + save: maybe 0.5s. Fine.

Let me write the final code.

```python
import random
import sys

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

_LARGE_VOCAB = 60000
_SMALL_VOCAB = 5000

_TOKENIZER_LARGE = WORKDIR / "tokenizer_large.json"
_TOKENIZER_SMALL = WORKDIR / "tokenizer_small.json"


def _build_tokenizer(path, vocab_size):
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i in range(vocab_size):
        vocab[f"tok{i}"] = len(vocab)
    tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    tok.save(str(path))


_build_tokenizer(_TOKENIZER_LARGE, _LARGE_VOCAB)
_build_tokenizer(_TOKENIZER_SMALL, _SMALL_VOCAB)


def _query(n_words, seed, unknown_ratio=0.0):
    rng = random.Random(seed)
    words = []
    for i in range(n_words):
        if rng.random() < unknown_ratio:
            words.append(f"zz{rng.randrange(10**9)}")
        else:
            words.append(f"tok{rng.randrange(_LARGE_VOCAB)}")
    return " ".join(words)


def _setup(argv):
    sys.argv = list(argv)
    return ()


def _argv(query, tokenizer, extra=()):
    return ["encode_query.py", query, "--tokenizer", str(tokenizer)] + list(extra)


def checks():
    return [
        ("empty-query", lambda: _setup(_argv("", _TOKENIZER_SMALL))),
        ("single-token", lambda: _setup(_argv("tok0", _TOKENIZER_SMALL))),
        ("cosine-empty", lambda: _setup(_argv("", _TOKENIZER_SMALL, ["--cosine"]))),
    ]


def cases():
    q_tiny = _query(4, 0)
    q_short = _query(40, 1)
    q_med = _query(800, 2)
    q_long = _query(20000, 3)
    q_huge = _query(40000, 4)
    q_mixed = _query(3000, 5, unknown_ratio=0.4)
    q_uni = " ".join(f"tok{i}" for i in range(0, 2000))  # hmm, pattern

    return [
        ("default-short-large", lambda: _setup(_argv(q_short, _TOKENIZER_LARGE))),
        ("default-long-large", lambda: _setup(_argv(q_long, _TOKENIZER_LARGE))),
        ("default-huge-small", lambda: _setup(_argv(q_huge, _TOKENIZER_SMALL))),
        ("default-mixed", lambda: _setup(_argv(q_mixed, _TOKENIZER_LARGE, ["--hits", "100"]))),
        ("rerank-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--rerank"]))),
        ("rerank-long", lambda: _setup(_argv(q_long, _TOKENIZER_SMALL, ["--rerank"]))),
        ("lexical-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--lexical"]))),
        ("cosine-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--cosine"]))),
    ]
```

Hmm, q_uni is unused; remove. Also "Avoid uniformity or patterns" — _query uses random, good.

Wait, `q_huge = _query(40000, 4)` with large vocab → but used with small tokenizer. That's fine, just many UNKs. Actually the encode cost is proportional to number of words, not vocab. 40000 words → maybe 30-50ms. Good.

Hmm, but for rerank-long with q_long (20000 words) and small tokenizer, the body includes the query string of 20000*~6 = 120KB. JSON dump of 120KB. Fine.

Let me reconsider: is 40000 words too slow? Whitespace splitting 40000 words + 40000 dict lookups. Maybe 30ms. Plus from_file ~10ms. Total ~40ms. Fine, under 200ms.

Actually let me be careful about the upper bound 200ms. Let me keep max query at 40000 words. Should be OK. Actually, let me reduce to 30000 to be safe.

Hmm, also the query string built with 40000 words: `" ".join(...)` — fine.

Let me reconsider `_query` with unknown_ratio: for q_mixed, 3000 words. Fine.

Let me finalize with q_huge = 30000.

Also, I should double check: does `Whitespace` pretokenizer exist in the tokenizers package version? Yes, `tokenizers.pre_tokenizers.Whitespace`.

Now, potential issue: `Tokenizer(WordLevel(...))` — the WordLevel model in newer versions requires `unk_token` to be in vocab. We have it. Good.

Another potential issue: `tok.save()` might need `tokenizers` version supporting it. Yes.

Let me also verify: `tok.token_to_id("[PAD]")` returns 0. Good.

`tok.enable_truncation(max_length=64)` and `enable_padding(length=64, pad_id=0, pad_token="[PAD]")`. Good.

Now, one concern: after enabling padding, encoding a query of 40000 words → truncation to 64 → padding to 64. The output ids length 64. Good.

Now let me also think: does the original function's `np.array(enc.ids, dtype=np.float32).tolist()` produce a list of 64 floats. Good.

Alright.

One more: for the cosine case, `args.tokenizer` default is used but never read. Fine. Actually we pass --tokenizer anyway.

Now checks: "empty-query" with `_argv("", _TOKENIZER_SMALL)`. sys.argv = ["encode_query.py", "", "--tokenizer", path]. parse_args: query="", --tokenizer=path. Good.

Hmm, but with an empty query, Whitespace produces zero tokens. Then `enable_padding(length=64)` pads to 64. Should work. But what if it raises? Then both versions raise identically — allowed.

Actually, hmm, will `tok.encode("")` with padding raise? I don't think so. Fine.

Let me also add a check with an odd type? main takes no args. The query is a string from argv. An "odd type" could be... nothing really. Let's keep 3 checks.

Actually, maybe a check where the tokenizer file doesn't exist → sys.exit. That's a different path. Let's add:

```python
("missing-tokenizer", lambda: _setup(_argv("hello", WORKDIR / "nope.json"))),
```

This calls sys.exit which raises SystemExit. Allowed ("These may raise"). And it tests the pad_id None / from_file error path. Actually from_file on a nonexistent file raises an exception. Both versions same. OK, but the instruction says checks "may raise". Fine.

Hmm, but it might be risky if the harness treats exceptions badly. It says "These may raise." So OK.

Let me include it. Actually, let me keep it to valid-ish edge cases to be safe. I'll include empty, single-token, and cosine-empty. Maybe add missing-tokenizer as a 3rd... Let's do 3: empty-query, single-token, missing-tokenizer. Hmm.

Actually, "empty, one element, None, an odd type". Let's do:
- empty query
- single token query
- cosine with empty query (different path)

I'll go with these 3.

Hmm, but the missing-tokenizer check is a nice edge. Let me include 3 and make one of them the missing file. Actually the instruction says 2 or 3. Let me do 3: empty, single-token, missing-tokenizer.

Hmm, but "missing-tokenizer" — does the harness check that both raise the same? "checked only for identical behaviour". If both raise the same exception type, identical. OK.

I'll go with empty-query, single-token, cosine-empty. Safer (no exceptions).

Hmm, let me include missing-tokenizer too... no, max 3. Let me pick: empty-query, single-token, missing-tokenizer. These cover: empty input, minimal input, error path.

Actually, cosine-empty covers a distinct code path (no tokenizer). Let me do: empty-query, single-token, cosine-empty. Final.

Hmm, actually I realize for checks, if a check raises, does the harness compare exceptions? "checked only for identical behaviour, never measured. These may raise." So yes, it compares.

OK final.

Let me write out the complete code.

Wait, I need to double-check: the `_setup` function returns `()`. The thunk `lambda: _setup(...)` returns `()`. The harness calls `main()`. Good.

But hold on — the thunk "returns a tuple of positional arguments for the function". `_setup` returns `()`. Good.

Now, is it OK that `_setup` has side effects (setting sys.argv)? Yes, setup is in the thunk.

Let me write it.

Actually, one more consideration: `sys.argv` needs to be a list of strings. We pass strings. Good.

Also, argparse with `--tokenizer` path containing special chars? WORKDIR path should be fine.

Let me finalize.

Also need `import sys` — yes.

Let me write the final block.

def cases(): building queries at call time. Fine.

Let me reconsider the number of words for each case to ensure variety in cost:
- q_short = 40 words
- q_med = 800 words
- q_long = 20000 words
- q_huge = 30000 words
- q_mixed = 3000 words (40% unknown)

Cases:
1. default-short-large: 40 words, large tokenizer → ~load 10ms + encode 0.1ms
2. default-long-large: 20000 words, large → ~10ms + 20ms
3. default-huge-small: 30000 words, small → ~2ms + 30ms
4. default-mixed-hits100: 3000 words, large, hits=100 → ~10ms + 3ms
5. rerank-medium: 800 words, large → ~10ms
6. rerank-long: 20000 words, small → ~2ms + 20ms + json dump 120KB
7. lexical-medium: 800 words, large → ~10ms
8. cosine-medium: 800 words, large, cosine → ~0.1ms (no tokenizer)

Good variety.

Hmm, case 8 (cosine) is very fast. It'll be dropped. That's fine.

Actually, maybe replace cosine with something heavier? But cosine is a distinct code path worth including. The harness keeps 4. Let's keep it.

Hmm, but if cosine is dropped, we still have 7 others. Fine.

Actually, let me make cosine use a huge query so the json.dump of the query is heavy. q_huge with cosine → body["q"] = 30000-word string (~200KB). json.dump of that. Hmm, that's actually some work. Let's do cosine with q_long (20000 words). Then it does json.dump of a 120KB string. Maybe 1-2ms. Still fast but not trivial.

Let me use q_huge for cosine? 30000 words → 200KB string dump. Eh.

I'll use q_long for cosine.

Let me finalize.

Final code:

```python
import random
import sys

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

_LARGE_VOCAB = 60000
_SMALL_VOCAB = 5000

_TOKENIZER_LARGE = WORKDIR / "tokenizer_large.json"
_TOKENIZER_SMALL = WORKDIR / "tokenizer_small.json"


def _build_tokenizer(path, vocab_size):
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i in range(vocab_size):
        vocab[f"tok{i}"] = len(vocab)
    tok = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    tok.save(str(path))


_build_tokenizer(_TOKENIZER_LARGE, _LARGE_VOCAB)
_build_tokenizer(_TOKENIZER_SMALL, _SMALL_VOCAB)


def _query(n_words, seed, unknown_ratio=0.0):
    rng = random.Random(seed)
    words = []
    for _ in range(n_words):
        if rng.random() < unknown_ratio:
            words.append("zz%d" % rng.randrange(10**9))
        else:
            words.append("tok%d" % rng.randrange(_LARGE_VOCAB))
    return " ".join(words)


def _setup(argv):
    sys.argv = list(argv)
    return ()


def _argv(query, tokenizer, extra=()):
    return ["encode_query.py", query, "--tokenizer", str(tokenizer)] + list(extra)


def checks():
    return [
        ("empty-query", lambda: _setup(_argv("", _TOKENIZER_SMALL))),
        ("single-token", lambda: _setup(_argv("tok0", _TOKENIZER_SMALL))),
        ("cosine-empty", lambda: _setup(_argv("", _TOKENIZER_SMALL, ["--cosine"]))),
    ]


def cases():
    q_short = _query(40, 1)
    q_med = _query(800, 2)
    q_long = _query(20000, 3)
    q_huge = _query(30000, 4)
    q_mixed = _query(3000, 5, unknown_ratio=0.4)

    return [
        ("default-short-large", lambda: _setup(_argv(q_short, _TOKENIZER_LARGE))),
        ("default-long-large", lambda: _setup(_argv(q_long, _TOKENIZER_LARGE))),
        ("default-huge-small", lambda: _setup(_argv(q_huge, _TOKENIZER_SMALL))),
        ("default-mixed-hits100", lambda: _setup(_argv(q_mixed, _TOKENIZER_LARGE, ["--hits", "100"]))),
        ("rerank-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--rerank"]))),
        ("rerank-long-small", lambda: _setup(_argv(q_long, _TOKENIZER_SMALL, ["--rerank"]))),
        ("lexical-medium", lambda: _setup(_argv(q_med, _TOKENIZER_LARGE, ["--lexical"]))),
        ("cosine-long", lambda: _setup(_argv(q_long, _TOKENIZER_LARGE, ["--cosine"]))),
    ]
```

That's 8 cases. Good.

Wait, I should double check that `Tokenizer` is importable and `WordLevel` too. The repository imports `from tokenizers import Tokenizer`. So tokenizers is installed. `tokenizers.models.WordLevel` and `tokenizers.pre_tokenizers.Whitespace` are standard submodules. Good.

One risk: `tok.save` might not exist in older versions — but it's been there for a long time.

Another risk: `WordLevel(vocab=..., unk_token=...)` — in some versions the signature is `WordLevel(vocab=None, unk_token=None)`. Keyword args work.

OK.

Let me also double check: the `Whitespace` pretokenizer handles the query with spaces. Good.

I think we're good. Let me write the final answer.

Actually, one thing: the harness might run the module-level code and then call cases(). Building two tokenizers: 60k + 5k vocab. Save time maybe 0.5s. Under 10s. Good.

Also memory: 60k dict entries, small.

Done.